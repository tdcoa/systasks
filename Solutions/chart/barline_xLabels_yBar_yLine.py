import sys

def coaprint(*args):
    # print(*args)
    return None

def human_format(num, pos):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.00
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

def args2dict(args):
    # args = ['file:bq--join_frequency.csv','title:Join Frequency', 'height:6', 'width:12', 'dateadjust:0.5', 'pancake', 'foo:bar:bam']
    kwargs = {}

    for arg in args:
        goodsyntax = False

        if ':' in arg:
            argobj = arg.split(':')
            if len(argobj) >1:
                kwargs[argobj[0]] = arg[len(argobj[0])+1:]
                goodsyntax = True

        if not goodsyntax:
            coaprint('Supplied arg not conformed to name:value syntax requirements:\t%s' %str(arg))

    if 'barlogscale' not in kwargs and 'logscale' in kwargs: kwargs['barlogscale']=kwargs['logscale']
    if 'yintercept' not in kwargs and 'ymin' in kwargs: kwargs['yintercept']=kwargs['ymin']
    if 'csvfile' not in kwargs and 'file' in kwargs:  kwargs['csvfile']=kwargs['file']
    return dict(kwargs)





def barline_xLabels_yBar_yLine(**kwargs):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    import matplotlib.patches as mpatches
    from datetime import date
    default_colors = ['#27C1BD','black','blue','yellow','orange','purple']
    formatter = FuncFormatter(human_format)

    # define all variables, with defaults
    errorcondition = False

    if 'csvfile' not in kwargs: errorcondition = True
    else: csvfile = kwargs['csvfile']

    if 'title' in kwargs: title = kwargs['title']
    elif not(errorcondition): title = csvfile.split('.')[0].split('--')[-1].replace('_',' ').upper()

    if 'height' in kwargs: height = float(kwargs['height'])
    elif not errorcondition: height = 6

    if 'width' in kwargs: width = float(kwargs['width'])
    elif not errorcondition: width = 12

    if 'save' in kwargs: save = bool(kwargs['save'])
    elif not errorcondition: save = True

    if 'sort' in kwargs: sort = int(kwargs['sort'])
    elif not errorcondition: sort = 0

    if 'barlogscale' in kwargs: barlogscale = bool(str(kwargs['barlogscale']).strip().lower()=='true')
    elif not errorcondition: barlogscale = False


    if errorcondition:
        msg = 'Error occurred while validating parameters, please check your parameters, documentation, and try again. \nParameters: %s' %str(kwargs)
        coaprint(msg)
        return msg


    # BUILD OUT X-AXIS (always first column // index 0)
    df = pd.read_csv(csvfile, thousands=',')
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    if sort !=0: df = df.sort_values(by=df.columns[sort-1])
    x = df[df.columns[0]]
    coaprint('x axis column: ', title)

    # BUILD OUT Y-AXIS COLLECTION
    ys=[]
    for col in df.columns[1:]:
        id = len(ys)+1  # x-axis is index 0
        series = df.iloc[:,id].astype(int)
        name = df.iloc[:,id].name
        color = default_colors[id-1]
        if '--' in name:
            color = name.split('--')[1].lower()
            name  = name.split('--')[0]
        graph_type = 'bar' if ys==[] else 'line'
        ys.append({'id':id, 'name':name, 'color':color, 'series':series, 'graph_type':graph_type})
        coaprint('y axis information: ', id, name, color, graph_type)


    # BUILD THE GRAPH FIGURE, ASSIGN SETTINGS
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_subplot(1,1,1)
    ax.margins(0.01)
    ax.yaxis.grid(True) # turn on yaxis vertical lines

    firstline = True
    for y in ys:
        if y['graph_type']=='bar':
            ax.bar(x, y['series'], label=y['name'], color=y['color'], linewidth=2)
            ax.tick_params(axis='y', color=y['color'])
            if barlogscale:
                ax.set_yscale('log')
                ax.set_ylim(ymin=1)
            else:
                ax.set_ylim(ymin=0)
            plt.ylabel(y['name'], color=y['color'])
            axbar = ax
        else:
            if firstline: ax = ax.twinx()
            firstline = False
            ax.tick_params(axis='y', colors='grey')
            ax.plot(x, y['series'], label=y['name'], color=y['color'], linewidth=2)
            if barlogscale:
                ax.set_yscale('linear')
                ax.set_ylim(ymin=1)


        y['handle'] = ax
        ax.tick_params(axis='y', colors=y['color'])
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_color('gray')
        plt.xticks(fontsize=10, rotation=0)
        if not barlogscale:
            ax.set_ylim(ymin=0)
            ax.set_yticks(np.linspace(ax.get_yticks()[0], ax.get_yticks()[-1], len(axbar.get_yticks())))
        ax.set_ylabel(y['name'], color=y['color'])
        ax.xaxis.label.set_color('grey')
        ax.tick_params(axis='x', colors='grey')
        ax.yaxis.set_major_formatter(formatter)

    # build final plot
    lgnd = []
    for y in ys:
        lgnd.append( mpatches.Patch(color=y['color'],label=y['name']))
    lgd = ax.legend(handles=lgnd, loc='upper center', bbox_to_anchor=(0.5, -0.2), shadow=True, ncol=5)

    plt.xticks(x)  # forces all values to be displayed
    plt.title(title, fontsize=14, y=1.0, pad=30, color='grey')

    # turn all backgrounds transparent
    for item in [fig, ax]:
        item.patch.set_visible(False)

    if save:
        plt.savefig(csvfile.replace('.csv','.png'), bbox_extra_artist=lgd, bbox_inches='tight')
    else:
        plt.show()





# build and export the graph
# args = ['file:bq--join_frequency.csv','title:Join Frequency', 'height:6', 'width:12', 'dateadjust:1', 'pancake', 'foo:bar:bam']
# barline_xLabels_yBar_yLine(**args2dict(args))
barline_xLabels_yBar_yLine(**args2dict(sys.argv[1:]))
