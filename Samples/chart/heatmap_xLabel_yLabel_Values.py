import coaVizLib, sys, os
from pathlib import Path

try:
    # setup visualization environment:
    coaLog = coaVizLib.coaLog('i')
    coaLog.addhandler('program debug log', 'd', Path(Path(os.getcwd()) / '{time} - Chart_Detail.log'))
    log = coaLog.log
    arg = coaVizLib.coaArg(log, sys.argv[1:], coaVizLib.getJsonFilePath(sys.argv[0]))
    data = coaVizLib.coaData(log, arg)
    plt = coaVizLib.Prework(log, arg, data)


    ### ========== START CHART-SPECIFIC CODE ========== ###
    import seaborn as sns
    import matplotlib.colors as clr

    log.info('STARTING CHARTING PROCESS: HEATMAP: heatmap_xLabel_yLabel_Values')
    log.info('Performing required dataframe pivot... ')
    colaxis = [data.dfx.iloc[:,0].name,  data.dfy.iloc[:,0].name ]
    coldata = data.dfy.iloc[:,1].name
    dfh = data.dfmain.groupby(by=colaxis)[coldata].sum().unstack().fillna(0)

    # define custom colormap:
    log.debug('Applying Colors to HeatMap\nNOTE: Heatmaps apply colors per value, not series, so we reset here to recover used custom colors')
    data.colors.reset()
    colorlist = list(data.colors.getnextcolors( arg.heatmapcolorcount ))
    cmap = clr.LinearSegmentedColormap.from_list("", colorlist)
    sns.heatmap(dfh.T, cmap=cmap, annot=arg.annotate, fmt='.0f', vmin=0, vmax=100, annot_kws={'fontsize': 10})
    plt.gca().tick_params(axis='y', labelrotation = 0)

    # turn off unwanted options:
    arg.xlabelflex = 0
    arg.legendxy = (0,0)
    ### ========== END CHART-SPECIFIC CODE ========== ###


    plt = coaVizLib.Postwork(log, arg, data, plt)

except Exception as ex:
    log.exception('ERROR OCCURED DURING CHART GENERATION, SKIPPING...')
