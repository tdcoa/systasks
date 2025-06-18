import importlib.util
import sys, os
from pathlib import Path

lib_path = Path(__file__).parent / "coaVizLib.py"
spec = importlib.util.spec_from_file_location("coaVizLib", lib_path)
coaVizLib = importlib.util.module_from_spec(spec)
sys.modules["coaVizLib"] = coaVizLib
spec.loader.exec_module(coaVizLib)

version = 1.1

try:
    # setup visualization environment:
    coaLog = coaVizLib.coaLog('i')
    logfilename = '{time}-v%s - heatmap_xLabel_yLabel_Values.log' %str(version).replace('.','_')
    coaLog.addhandler('program debug log', 'd', Path(Path(os.getcwd()) / logfilename ))
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

    # set min/max values for color, if not defined already
    if str(arg.heatmapmin).lower().strip() == '<<min of data>>':
        log.debug('heatmapmin not set, so defaulting to the minimum value found across all data')
        arg.heatmapmin = int(dfh.min().min())
        log.debug('heatmapmin set to %i' %arg.heatmapmin)

    if str(arg.heatmapmax).lower().strip() == '<<max of data>>':
        log.debug('heatmapmax not set, so defaulting to the maximum value found across all data')
        arg.heatmapmax = int(dfh.max().max())
        log.debug('heatmapmax set to %i' %arg.heatmapmax)

    # define custom colormap:
    log.debug('Applying Colors to HeatMap\nNOTE: Heatmaps apply colors per value, not series, so we reset here to recover used custom colors')
    data.colors.reset()
    colorlist = list(data.colors.getnextcolors( arg.heatmapcolorcount ))
    cmap = clr.LinearSegmentedColormap.from_list("", colorlist)
    sns.heatmap(dfh.T, cmap=cmap, annot=arg.annotate, fmt='.0f', vmin=arg.heatmapmin, vmax=arg.heatmapmax, annot_kws={'fontsize': 10})
    plt.gca().tick_params(axis='y', labelrotation = 0)

    # turn off unwanted options:
    arg.xlabelflex = 0
    arg.legendxy = (0,0)
    ### ========== END CHART-SPECIFIC CODE ========== ###

    plt = coaVizLib.Postwork(log, arg, data, plt)

except Exception as e:
    msg = 'ERROR OCCURED DURING CHART GENERATION of file: %s\n%s' %(str(arg.pngfilepath), str(e))
    if len(data.dfmain)==0:
        msg = msg + '\n\nNOTE: DataFrame ("%s") contained no data, maybe you want to check that out.\n\n' %str(arg.csvfilepath)
    msg = msg + 'Final argument list, for your reading pleasure\n  (for more detail, see log file: "%s"):\n\n%s' %(coaLog.logfilename, arg.dictdisplay(arg.__dict__))

    log.error(msg)
    coaVizLib.make_empty_chart(str(arg.pngfilepath), msg)
finally:
    sys.exit(0)
