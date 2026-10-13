"""vhc_workload_risk.py -- derive the VHC "Workload Usage Trends & Shifts" slide data.

Reads  vhc--workload_usage.csv  (exported only when include_wdname is on) from the
current output folder and writes the three files the slide's placeholders read:

  vhc--workload_summary.csv   one row of headline values      ({{val:...}} tags)
  vhc--workload_risk.csv      header + 8 rows for the table    ({{col:...}} tags)
  vhc--workload_trend.png     weekly CPU trend, top 5 + Other  ({{pic:...}} tag)

Run this task UNCONDITIONALLY (outside the {% if 'Workload_Definition' ... %} block).
When the source CSV is absent the script still writes all three files with a
"not collected" message, so the PPT build never fails on a missing data file.

How it reads the pattern: each workload's CPU is bucketed into full weeks (CPU hours
per day, averaged over the week) across the whole run, then three things are measured:
  Trend          robust slope through every week (Theil-Sen), as % of the workload's
                 average per 4 weeks -- one unusual week cannot swing it
  Biggest shift  the single week where the level changed most (best two-level fit),
                 with its size and date -- migrations usually look like a step
  vs peak        the last 2 weeks against the workload's own peak week -- catches
                 workloads that ramped up and then faded
Workloads stepping down and others stepping up (or appearing) within a week of each
other are reported as "moved in the same week" -- a hint that work moved, not proof.

Parameters are optional "name:value" pairs (same style as build_oap_json.py):
  step_pct:30          a shift of at least this % is a Step down / Step up
  trend_pct:15         a trend of at least this % per 4 weeks is Steady decline / growth
  faded_pct:50         last 2 weeks this % or more below the peak week is Faded from peak
  spike_ratio:3        a week above this multiple of the median week is a One-off spike
  min_share_pct:1      ignore workloads below this share of CPU (whole run, or last 2 weeks)
  silent_days:7        Inactive when no CPU in the last N days of data
  concentration_pct:30 note a single workload above this CPU share
  delay_pct:25         note workloads with more than this % of requests delayed
                       (TASM throttles delay requests on purpose, so keep this high)
  top_n:5              workloads drawn individually on the trend chart
"""
import csv
import statistics as st
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SRC = 'vhc--workload_usage.csv'
OUT_SUMMARY = 'vhc--workload_summary.csv'
OUT_RISK = 'vhc--workload_risk.csv'
OUT_PNG = 'vhc--workload_trend.png'
TABLE_ROWS = 8
COLORS = ["#27C1BD", "#EC8D1A", "#038DAC", "#EEA200", "#7B4FA0", "#B5B5B5"]

DEFAULTS = {'step_pct': 30.0, 'trend_pct': 15.0, 'faded_pct': 50.0, 'spike_ratio': 3.0,
            'min_share_pct': 1.0, 'silent_days': 7, 'concentration_pct': 30.0,
            'delay_pct': 25.0, 'top_n': 5}

SUMMARY_COLS = ['Status', 'Active_Workloads', 'Top5_CPU_Share', 'Declining_Cnt', 'Growing_New_Cnt',
                'Inactive_Cnt', 'Top_Workload', 'Top_Workload_Share', 'Period', 'Weeks',
                'Thresholds', 'Other_Flags', 'Period_Line',
                'Flag_Together', 'Flag_Concentration', 'Flag_Delay']
RISK_HEADER = ['Workload', 'CPU Share', '4-wk trend', 'Biggest shift', 'Pattern']
DECLINING = ('Step down', 'Steady decline', 'Faded from peak', 'Inactive')
GROWING = ('Step up', 'Steady growth', 'New')

# NOTE: keep every literal ASCII -- tdcoa reads these CSVs with the OS default
# encoding (cp1252 on Windows), so UTF-8 symbols arrive as mojibake on the slide.


def parse_params(argv):
    p = dict(DEFAULTS)
    for arg in argv:
        if ':' not in arg:
            continue
        k, v = arg.split(':', 1)
        k = k.strip().lower()
        if k in p:
            try:
                p[k] = type(DEFAULTS[k])(float(v))
            except ValueError:
                print(f'ignoring bad parameter {arg!r}')
    return p


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def load(path):
    rows = []
    with path.open(newline='', errors='replace') as f:   # same default encoding as tdcoa's load_csv
        rd = csv.DictReader(f)
        if not rd.fieldnames or 'Workload_Definition' not in rd.fieldnames or 'LogDate' not in rd.fieldnames:
            return rows
        for r in rd:
            try:
                d = date.fromisoformat(r['LogDate'].strip()[:10])
            except ValueError:
                continue
            rows.append((d, (r.get('Workload_Definition') or 'Unknown').strip() or 'Unknown',
                         fnum(r.get('CPU_Total_Sec')), fnum(r.get('Request_Total_Cnt')),
                         fnum(r.get('Request_Delayed_Cnt'))))
    return rows


def pct(x):
    return f'{x:.1f}%'


def write_csv(name, header, rows):
    with open(name, 'w', newline='') as f:   # default encoding, matching tdcoa's load_csv
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def message_png(text):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=150)
    ax.axis('off')
    ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=12, color='#636363', wrap=True)
    fig.savefig(OUT_PNG, bbox_inches='tight', transparent=True)
    plt.close(fig)


def not_enabled(reason):
    msg = f'Workload metrics not collected for this run ({reason}). Delete this slide.'
    write_csv(OUT_SUMMARY, SUMMARY_COLS, [[msg] + ['n/a'] * (len(SUMMARY_COLS) - 5) + [msg, '', '', '']])
    write_csv(OUT_RISK, RISK_HEADER, [['n/a'] + [''] * 4] + [[''] * 5 for _ in range(TABLE_ROWS - 1)])
    message_png('Workload metrics were not collected for this run.\n'
                'Re-run with include_wdname = True, or delete this slide.')
    print(msg)


def theil_sen(y):
    s = [(y[j] - y[i]) / (j - i) for i in range(len(y)) for j in range(i + 1, len(y))]
    return st.median(s) if s else 0.0


def best_step(y):
    """best two-level fit: (split index, level before, level after, fit quality 0..1)"""
    n = len(y)
    edge = 2 if n >= 5 else 1
    m = st.mean(y)
    sst = sum((v - m) ** 2 for v in y)
    best = None
    for s in range(edge, n - edge + 1):
        a, b = st.mean(y[:s]), st.mean(y[s:])
        sse = sum((v - a) ** 2 for v in y[:s]) + sum((v - b) ** 2 for v in y[s:])
        if best is None or sse < best[0]:
            best = (sse, s, a, b)
    if best is None or sst == 0:
        return None
    sse, s, a, b = best
    return s, a, b, 1.0 - sse / sst


def trend_png(weeks, series, top):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    other = [sum(series[w][i] for w in series if w not in top) for i in range(len(weeks))]
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=150)
    for i, wd in enumerate(list(top) + ['Other']):
        ys = other if wd == 'Other' else series[wd]
        ax.plot(weeks, ys, label=wd, color=COLORS[i % len(COLORS)], linewidth=2.2 if wd != 'Other' else 1.6,
                linestyle='-' if wd != 'Other' else '--', marker='o', markersize=3)
    ax.set_ylabel('CPU hours / day (weekly avg)', fontsize=8, color='#636363')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.tick_params(labelsize=7, colors='#636363')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.grid(axis='y', color='#E5E5E5', linewidth=0.6)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=7, ncol=3, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.12))
    fig.savefig(OUT_PNG, bbox_inches='tight', transparent=True)
    plt.close(fig)


def main():
    p = parse_params(sys.argv[1:])
    src = Path(SRC)
    if not src.exists():
        return not_enabled('include_wdname was off')
    rows = load(src)
    if not rows:
        return not_enabled('workload export was empty')

    first = min(r[0] for r in rows)
    last = max(r[0] for r in rows)
    nweeks = max(1, ((last - first).days + 1) // 7)          # full weeks only; a partial tail is dropped
    weeks = [first + timedelta(weeks=i) for i in range(nweeks)]
    week_end = weeks[-1] + timedelta(days=6)
    silent_start = last - timedelta(days=p['silent_days'] - 1)

    series = defaultdict(lambda: [0.0] * nweeks)               # CPU hours / day, per week
    tot = defaultdict(float); req = defaultdict(float); dly = defaultdict(float); silent = defaultdict(float)
    for d, wd, cpu, rq, dl in rows:
        tot[wd] += cpu; req[wd] += rq; dly[wd] += dl
        if d >= silent_start:
            silent[wd] += cpu
        k = (d - first).days // 7
        if k < nweeks:
            series[wd][k] += cpu / 3600.0 / 7.0
    for wd in tot:
        series[wd]                                             # every workload gets a (maybe zero) series
    grand = sum(tot.values()) or 1.0
    share = {k: 100.0 * v / grand for k, v in tot.items()}
    recent_tot = sum(sum(y[-2:]) for y in series.values()) or 1.0
    recent_share = {k: 100.0 * sum(y[-2:]) / recent_tot for k, y in series.items()}
    ranked = sorted(tot, key=lambda k: -tot[k])
    top = ranked[:p['top_n']]
    fmtw = lambda d: f'w/c {d:%d %b}'

    info = {}
    event_week = {}                                            # week index of each workload's main shift
    for wd, y in series.items():
        material = share[wd] >= p['min_share_pct'] or recent_share.get(wd, 0) >= p['min_share_pct']
        m = st.mean(y)
        trend = 100.0 * theil_sen(y) * 4 / m if m else 0.0
        stp = best_step(y) if nweeks >= 3 else None
        peak = max(y)
        last2 = st.mean(y[-2:]) if nweeks >= 2 else y[-1]
        med = st.median(y)
        pattern, shift, size = 'Stable', '', 0.0
        if stp:
            s, a, b, fit = stp
            chg = 100.0 * (b - a) / a if a else None
            shift = (f'new {fmtw(weeks[s])}' if chg is None else f'{chg:+.0f}% {fmtw(weeks[s])}')
        if not material:
            pattern = None
        elif silent[wd] == 0 and m > 0:
            pattern, size = 'Inactive', m
        elif nweeks >= 4 and max(y[:2]) <= 0.05 * st.median(y[2:]) and last2 > 0:
            ref = st.median(y[2:])
            nz = next(i for i, v in enumerate(y) if v > 0.05 * ref)
            pattern, shift, size = 'New', f'new {fmtw(weeks[nz])}', last2
            event_week[wd] = nz
        elif peak > p['spike_ratio'] * max(med, 1e-9) and (not stp or stp[3] < 0.6) \
                and abs(trend) < p['trend_pct'] * 2:
            pk = y.index(peak)
            pattern, shift, size = 'One-off spike', f'peak {fmtw(weeks[pk])}', 0.5 * (peak - med)
        elif stp and stp[3] >= 0.6 and stp[1] and abs(100.0 * (stp[2] - stp[1]) / stp[1]) >= p['step_pct']:
            pattern = 'Step down' if stp[2] < stp[1] else 'Step up'
            size = abs(stp[2] - stp[1])
            event_week[wd] = stp[0]
        elif trend <= -p['trend_pct']:
            pattern, size = 'Steady decline', abs(theil_sen(y) * (nweeks - 1))
        elif trend >= p['trend_pct']:
            pattern, size = 'Steady growth', abs(theil_sen(y) * (nweeks - 1))
        elif peak > 0 and y.index(peak) >= 2 and 100.0 * (last2 - peak) / peak <= -p['faded_pct']:
            pk = y.index(peak)
            pattern, shift, size = 'Faded from peak', f'{100.0 * (last2 - peak) / peak:+.0f}% vs peak {fmtw(weeks[pk])}', peak - last2
        info[wd] = dict(pattern=pattern, trend=trend, shift=shift, size=size, step=stp)

    # moved in the same week: workloads stepping down and others stepping up (or appearing)
    # within a week of each other -- a hint that work moved, not proof of it
    events = sorted((event_week[wd], wd, info[wd]['pattern'] in ('Step down',), info[wd]['size'])
                    for wd in event_week)
    groups = []
    for ev in events:
        if groups and ev[0] - groups[-1][0][0] <= 1:
            groups[-1].append(ev)
        else:
            groups.append([ev])
    together = []
    for g in groups:
        downs = [e for e in g if e[2]]; ups = [e for e in g if not e[2]]
        if downs and ups:
            name = lambda es: ', '.join(e[1] for e in sorted(es, key=lambda e: -e[3])[:3]) + \
                (f' +{len(es) - 3}' if len(es) > 3 else '')
            w0, w1 = weeks[g[0][0]], weeks[g[-1][0]]
            when = fmtw(w0) if w0 == w1 else f'w/c {w0:%d %b} - {w1:%d %b}'
            together.append((sum(e[3] for e in g), f'({when}): down {name(downs)}; up {name(ups)}'))
    together = [t for _, t in sorted(together, reverse=True)]

    extra = []
    f_together = f_conc = f_delay = ''
    if together:
        f_together = 'Moved together ' + ' | '.join(together[:2])
        extra.append(f_together)
    if share[ranked[0]] > p['concentration_pct']:
        f_conc = f"Concentration: {ranked[0]} uses {pct(share[ranked[0]])} of CPU"
        extra.append(f_conc)
    dpct = {wd: 100.0 * dly[wd] / req[wd] for wd in ranked if req[wd] > 0}
    pressured = sorted((wd for wd in dpct if dpct[wd] > p['delay_pct'] and share[wd] >= p['min_share_pct']),
                       key=lambda wd: -dpct[wd])
    if pressured:
        f_delay = (f"Delayed requests over {p['delay_pct']:.0f}%: "
                   + ', '.join(f'{wd} ({dpct[wd]:.0f}%)' for wd in pressured[:3])
                   + (f' +{len(pressured) - 3} more' if len(pressured) > 3 else ''))
        extra.append(f_delay)

    flagged = sorted((wd for wd, i in info.items() if i['pattern'] not in (None, 'Stable')),
                     key=lambda wd: (info[wd]['pattern'] == 'One-off spike', -info[wd]['size']))   # spikes rank after real shifts
    table = flagged[:TABLE_ROWS]
    for wd in ranked:
        if len(table) >= TABLE_ROWS:
            break
        if wd not in table and info[wd]['pattern'] is not None:
            table.append(wd)
    out = [[wd, pct(share[wd]), f"{max(-100.0, min(999.0, info[wd]['trend'])):+.0f}%", info[wd]['shift'] or '-', info[wd]['pattern']]
           for wd in table]
    while len(out) < TABLE_ROWS:
        out.append([''] * 5)
    write_csv(OUT_RISK, RISK_HEADER, out)

    cnt = lambda pats: sum(1 for i in info.values() if i['pattern'] in pats)
    period = f'{first:%d %b} - {week_end:%d %b %Y}'
    write_csv(OUT_SUMMARY, SUMMARY_COLS, [[
        'Workload metrics collected',
        str(len(tot)),
        pct(sum(share[w] for w in top)),
        str(cnt(DECLINING)),
        str(cnt(GROWING)),
        str(cnt(('Inactive',))),
        ranked[0],
        pct(share[ranked[0]]),
        period,
        str(nweeks),
        f"Step >= {p['step_pct']:.0f}%, steady trend >= {p['trend_pct']:.0f}% per 4 weeks, "
        f"faded >= {p['faded_pct']:.0f}% below peak, min share {p['min_share_pct']:.0f}%, "
        f"inactive = no CPU in last {p['silent_days']} days",
        '; '.join(extra) if extra else 'None',
        f'Weekly trend across {nweeks} full weeks: {period}',
        f_together, f_conc, f_delay,
    ]])
    trend_png(weeks, series, top)
    print(f'workload trends: {len(tot)} workloads, {len(flagged)} with a pattern, {nweeks} weeks, '
          f'{len(together)} same-week groups')


if __name__ == '__main__':
    main()
