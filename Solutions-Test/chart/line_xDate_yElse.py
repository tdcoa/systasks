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

    if 'yintercept' not in kwargs and 'ymin' in kwargs: kwargs['yintercept']=kwargs['ymin']
    if 'csvfile' not in kwargs and 'file' in kwargs:  kwargs['csvfile']=kwargs['file']
    return dict(kwargs)





def line_xDate_yElse(**kwargs):
    import numpy
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    from datetime import date
    default_colors = ['#27C1BD','#636363','#EC8D1A','#038DAC','#EEA200','purple','green']
    formatter = FuncFormatter(human_format)
    coaprint('line_xDate_yElse Started')
    coaprint('args:', kwargs)

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

    if 'save' in kwargs: width = bool(kwargs['save'])
    elif not errorcondition: save = True

    if 'yintercept' in kwargs: width = int(kwargs['yintercept'])
    elif not errorcondition: ylim = 0

    if 'dateadjust' in kwargs: dateadjust = float(kwargs['dateadjust'])
    elif not errorcondition: dateadjust = 1

    if errorcondition:
        msg = 'Error occurred while validating parameters, please check your parameters, documentation, and try again. \nParameters: %s' %str(kwargs)
        coaprint(msg)
        return msg


    # BUILD OUT X-AXIS (always first column // index 0)
    df = pd.read_csv(csvfile)
    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
    df = df.sort_values(by=df.columns[0])
    x = df[df.columns[0]]
    if title=='': title = csvfile.split('.')[0].split('--')[-1].replace('_',' ').upper()
    coaprint('x axis column: ', title)

    # BUILD OUT Y-AXIS COLLECTION
    ys=[]
    for col in df.columns[1:]:
        id = len(ys)+1  # x-axis is index 0
        series = df.iloc[:,id]
        name = series.name
        color = default_colors[id-1]
        if '--' in name:
            color = name.split('--')[1].lower()
            name  = name.split('--')[0]
        ys.append({'id':id, 'name':name, 'color':color, 'series':series})
        coaprint('y axis information: ', id, name, color)


    # BUILD THE GRAPH FIGURE, ASSIGN SETTINGS
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_subplot(1,1,1)
    ax.margins(0.01)
    ax.yaxis.grid(True) # turn on yaxis vertical lines
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


    # build final plot
    #fig.legend()
    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.3), shadow=True, ncol=5)
    plt.xticks(x)  # forces all values to be displayed
    ax.set_ylim(ymin=0)
    plt.title(title, fontsize=12, fontname='Arial', y=1.0, pad=30, color='grey')

    # turn all backgrounds transparent
    for item in [fig, ax]:
        item.patch.set_visible(False)

    # hide some xaxis label, if too many dates to display properly
    x = int(len(df)/width/(4*dateadjust))
    i = 0
    if x > 1:
        for label in ax.xaxis.get_ticklabels():
            coaprint('i = %i\nx = %i' %(i,x))
            label.set_visible(i%x==0)
            i+=1

    if save:
        plt.savefig(csvfile.replace('.csv','.png'), bbox_extra_artist=lgd, bbox_inches='tight')
    else:
        plt.show()


# build and export the graph
# args = ['file:bq--daily_query_throughput.csv','title:Query Throughtput', 'height:6', 'width:12', 'dateadjust:1', 'pancake', 'foo:bar:bam']
# line_xDate_yElse(**args2dict(args))
line_xDate_yElse(**args2dict(sys.argv[1:]))
