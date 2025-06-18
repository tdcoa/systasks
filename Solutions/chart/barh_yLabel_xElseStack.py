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
    logfilename = '{time}-v%s - barh_yLabel_xElseStack.log' %str(version).replace('.','_')
    coaLog.addhandler('program debug log', 'd', Path(Path(os.getcwd()) / logfilename ))
    log = coaLog.log
    arg = coaVizLib.coaArg(log, sys.argv[1:], coaVizLib.getJsonFilePath(sys.argv[0]))

    # custom... flip x/y axis before going into data & prework
    xcols = list(arg.xcolumns)
    arg.xcolumns = list(arg.ycolumns)
    arg.ycolumns = list(xcols)
    ###

    data = coaVizLib.coaData(log, arg)
    plt = coaVizLib.Prework(log, arg, data)


    ### ========== START CHART-SPECIFIC CODE ========== ###

    # iterate thru all columns in dfY and iterate / generate bar data:
    log.info('ready to generate stacked horizontal bar chart')
    bottom = [0 for z in data.dfy.iloc[:,0]]
    log.info('    left = %s' %str(bottom) )
    log.info('note: if you see an error that says something like: \n   %s\n   it means your csv is returning a TEXT type, not Number.  Maybe you have non-numerics mixed in, like commas or percent signs...?' %"--> unsupported operand type(s) for +: 'int' and 'str' <--")

    for itr, col in enumerate(data.dfy.columns):
        log.info('    building stack = %s' %str(data.dfy.loc[:,col].name) )
        ydata = list(data.dfy.loc[:,col])
        plt.barh(data.dfx.iloc[:,0],
                 ydata,
                 label = data.dfy.loc[:,col].name,
                 color = data.colormap['dfy'][col],
                 zorder = int(1/(itr+1)*100),
                 linestyle = '-',
                 linewidth = 2,
                 left = bottom)
        log.info('    stack built!  Re-calculating new left positions...' )
        bottom = [a + b for a,b in zip(bottom, ydata)]
        log.info('    new left = %s' %str(bottom) )

    log.info('    done stacking!' )
    xlabel = data.dfx.iloc[:,0].name if arg.xlabel == '<<column name>>' else arg.xlabel
    log.info('    xlabel = %s' %xlabel )
    plt.xlabel(arg.ylabel, fontsize = arg.labelsize, color='grey')
    plt.ylabel(xlabel, loc = "top", fontsize = arg.labelsize, color='grey')

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
