import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

def coaprint(*args):
    return None  # Replace with print(*args) for debugging

def human_format(num, pos):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

def args2dict(args):
    kwargs = {}
    for arg in args:
        if ':' in arg:
            key, value = arg.split(':', 1)
            kwargs[key] = value
    if 'yintercept' not in kwargs and 'ymin' in kwargs:
        kwargs['yintercept'] = kwargs['ymin']
    if 'csvfile' not in kwargs and 'file' in kwargs:
        kwargs['csvfile'] = kwargs['file']
    return kwargs

def line_xDate_yElse(**kwargs):
    default_colors = ['#27C1BD','#636363','#EC8D1A','#038DAC','#EEA200','purple','green','orange','red','blue','yellow','brown','black']
    formatter = FuncFormatter(human_format)

    if 'csvfile' not in kwargs:
        print("Missing required parameter: csvfile")
        return

    csvfile = kwargs['csvfile']
    title = kwargs.get('title', csvfile.split('.')[0].replace('_',' ').upper())
    height = float(kwargs.get('height', 6))
    width = float(kwargs.get('width', 12))
    save = kwargs.get('save', 'True').lower() == 'true'
    sort = int(kwargs.get('sort', 1))
    dateadjust = float(kwargs.get('dateadjust', 1))
    secondary_col = kwargs.get('secondary', None)

    df = pd.read_csv(csvfile)
    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
    if sort != 0:
        df = df.sort_values(by=df.columns[sort-1])
    x = df[df.columns[0]]

    ys = []
    for idx, col in enumerate(df.columns[1:], start=1):
        if col == secondary_col:
            continue
        series = df.iloc[:, idx]
        name = series.name
        color = default_colors[(idx - 1) % len(default_colors)]
        if '--' in name:
            name_parts = name.split('--')
            name = name_parts[0]
            color = name_parts[1].lower()
        ys.append({'name': name, 'color': color, 'series': series})

    fig, ax = plt.subplots(figsize=(width, height))
    ax.margins(0.01)
    ax.yaxis.grid(True)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_color('gray')
    plt.xticks(fontsize=8, rotation=90)

    for y in ys:
        ax.plot(x, y['series'], label=y['name'], color=y['color'], linewidth=2)
        ax.xaxis.label.set_color('grey')
        ax.tick_params(axis='x', colors='grey')
        ax.tick_params(axis='y', colors='grey')
        ax.yaxis.set_major_formatter(formatter)

    handles, labels = ax.get_legend_handles_labels()


    if secondary_col and secondary_col in df.columns:
        ax2 = ax.twinx()
        sec_series = df[secondary_col]

        # Hide spines for clean look
        for spine in ['top','left','bottom','right']:
            ax2.spines[spine].set_visible(False)

        # Main axis min/max
        main_min, main_max = ax.get_ylim()

        # Secondary axis min/max
        sec_min, sec_max = 0, int(np.ceil(sec_series.max()))

        # Map secondary data to main axis scale
        scaled_sec = main_min + (sec_series - sec_min) / (sec_max - sec_min) * (main_max - main_min)
        
        # Plot on main axis and include label for legend
        ax.plot(x, scaled_sec, label=secondary_col, color='blue', linestyle='--', linewidth=2)

        # Generate evenly spaced whole-number secondary ticks
        n_ticks = len(ax.get_yticks())
        sec_tick_values = np.linspace(0, sec_max, n_ticks).astype(int)
        ax2.set_yticks(main_min + (sec_tick_values - sec_min) / (sec_max - sec_min) * (main_max - main_min))
        ax2.set_ylim(main_min, main_max)
        
        # Format ticks and label
        ax2.yaxis.set_major_formatter(
            FuncFormatter(
                lambda x, _: f"{int(np.round(sec_min + (x - main_min)/(main_max - main_min)*(sec_max - sec_min)))}%"
            )
        )

        ax2.tick_params(axis='y', colors='grey')
        ax2.tick_params(axis='y', length=0)  # hide tick marks

        ax2.yaxis.set_label_position("right")
        ax2.yaxis.set_ticks_position("right")
        ax2.set_ylabel(secondary_col, color='grey', fontsize=10, labelpad=20, rotation=270)

    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.3), shadow=True, ncol=5)


    plt.xticks(x)
    ax.set_ylim(ymin=0)
    plt.title(title, fontsize=12, fontname='Arial', y=1.0, pad=30, color='grey')

    for item in [fig, ax]:
        item.patch.set_visible(False)

    x_density = int(len(df) / width / (4 * dateadjust))
    if x_density > 1:
        for i, label in enumerate(ax.xaxis.get_ticklabels()):
            label.set_visible(i % x_density == 0)

    if save:
        plt.savefig(csvfile.replace('.csv', '.png'), bbox_extra_artists=[lgd], bbox_inches='tight')
    else:
        plt.show()

if __name__ == '__main__':
    line_xDate_yElse(**args2dict(sys.argv[1:]))
