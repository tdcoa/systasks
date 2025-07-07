import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec


def coaprint(*args):
    # print(*args)
    return None


def human_format(num, pos=None):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.1f%s' % (num, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])


def args2dict(args):
    kwargs = {}
    for arg in args:
        if ':' in arg:
            k, v = arg.split(':', 1)
            if v.startswith('[') and v.endswith(']'):
                kwargs[k] = eval(v)
            else:
                kwargs[k] = v
    if 'csvfile' not in kwargs and 'file' in kwargs:
        kwargs['csvfile'] = kwargs['file']
    return kwargs


def barline_xLabels_yBar_yLine(**kwargs):
    # ---- Set defaults
    csvfile = kwargs.get('csvfile')
    pngfile = kwargs.get('pngfile', csvfile.replace('.csv', '.png'))
    title = kwargs.get('title', csvfile.split('.')[0].split('--')[-1].replace('_', ' ').upper())
    height = float(kwargs.get('height', 6))
    width = float(kwargs.get('width', 12))
    save = kwargs.get('save', True)
    if isinstance(save, str): save = save.lower() == 'true'
    xrotate = int(kwargs.get('xrotate', 0))
    barlogscale = kwargs.get('barlogscale', 'false').lower() == 'true'
    xcols = kwargs.get('xcolumns', [0])
    xcol_index = xcols[0] if isinstance(xcols, list) else eval(xcols)[0]

    ycols = kwargs.get('ycolumns', [1, 2])
    ycol_indices = ycols if isinstance(ycols, list) else eval(ycols)

    # ---- Load Data
    df = pd.read_csv(csvfile, thousands=',')
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df['xtick'] = df.iloc[:, xcol_index].astype(str)
    x = df['xtick']

    # ---- Separate Y data for bar chart vs table
    exclude_col = df.columns[xcol_index]

    # All columns for table (excluding the x-column)
    ycol_names_table = [col for col in df.columns if col != exclude_col and col != 'xtick']
    ys_table = []

    for col in ycol_names_table:
        try:
            ys_table.append([human_format(float(val)) if pd.notna(val) else '' for val in df[col]])
        except:
            # If conversion to float fails, keep as string
            ys_table.append([str(val) for val in df[col]])

    # User-defined Y columns for bar chart
    ycol_names_bar = [df.columns[i] for i in ycol_indices]
    ys = [df[name].astype(float) for name in ycol_names_bar]

    # ---- Extend bar colors if needed
    base_colors = ['#27C1BD', '#636363']
    colors = (base_colors * (len(ycol_names_bar) // len(base_colors) + 1))[:len(ycol_names_bar)]
    formatter = FuncFormatter(human_format)

    # ---- Create a taller figure to accommodate both chart and table
    fig = plt.figure(figsize=(width, height + 2))
    gs = gridspec.GridSpec(2, 1, height_ratios=[5, 1], hspace=0.2)

    # ---- Chart axis
    ax = fig.add_subplot(gs[0])
    ax.margins(0.01)
    ax.yaxis.grid(True)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_color('gray')

    bottom = np.zeros(len(df))
    lgnd = []

    for i, y in enumerate(ys):
        bar = ax.bar(x, y, bottom=bottom, color=colors[i], label=ycol_names_bar[i], linewidth=2)
        #for j, value in enumerate(y):
        #    if value > 0:
        #        ax.text(j, bottom[j] + value / 2, human_format(value), ha='center', va='center',
        #                fontsize=4.5, color='white')
        bottom += y
        lgnd.append(mpatches.Patch(color=colors[i], label=ycol_names_bar[i]))

    if barlogscale and all(bottom > 0):
        ax.set_yscale('log')
        ax.set_ylim(ymin=0.1)
    else:
        ax.set_ylim(ymin=0)

    ax.set_xticks(np.arange(len(df)))
    ax.set_xticklabels(x, rotation=xrotate, ha='center', fontsize=8)
    ax.tick_params(axis='x', colors='grey')
    ax.tick_params(axis='y', colors='grey')
    ax.yaxis.set_major_formatter(formatter)
    ax.set_ylabel(ycol_names_bar[0], color='grey')
    ax.set_title(title, fontsize=14, y=1.0, pad=30, color='grey')

    lgd = ax.legend(handles=lgnd, loc='upper center', bbox_to_anchor=(0.5, 1.05), frameon=False, ncol=len(lgnd),
                    fontsize=9)

    # ---- Table Axis
    table_ax = fig.add_subplot(gs[1])
    table_ax.axis('off')

    # Build table_data safely (format numbers, keep strings as-is)
    table_data = []
    for series in ys_table:
        row = []
        for val in series:
            try:
                val = float(val)
                row.append(human_format(val))
            except:
                row.append(str(val))  # keep non-numeric as-is
        table_data.append(row)

    row_labels = ycol_names_table

    the_table = table_ax.table(
        cellText=table_data,
        rowLabels=row_labels,
        loc='center',
        cellLoc='center',
        rowLoc='center'
    )

    the_table.auto_set_font_size(False)
    the_table.set_fontsize(5)

    # Make row labels (left column) larger
    for (row, col), cell in the_table.get_celld().items():
        if col == -1:  # -1 = row labels
            cell.get_text().set_fontsize(5.5)
            cell.get_text().set_fontweight('bold')

    for item in [fig, ax]:
        item.patch.set_visible(False)

    if save:
        plt.savefig(pngfile, bbox_inches='tight', transparent=True, bbox_extra_artists=[lgd])
    else:
        plt.show()


if __name__ == '__main__':
    kwargs = args2dict(sys.argv[1:])
    barline_xLabels_yBar_yLine(**kwargs)
