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
    logfilename = '{time}-v%s - bar_xLabel_yBar.log' %str(version).replace('.','_')
    coaLog.addhandler('program debug log', 'd', Path(Path(os.getcwd()) / logfilename ))
    log = coaLog.log
    arg = coaVizLib.coaArg(log, sys.argv[1:], coaVizLib.getJsonFilePath(sys.argv[0]))
    data = coaVizLib.coaData(log, arg)
    plt = coaVizLib.Prework(log, arg, data)


    ### ========== START CHART-SPECIFIC CODE ========== ###

    # iterate thru all columns in dfY and iterate / generate bar data:
    log.info('ready to generate vertical bar(s) chart')
    log.info('note: if you see an error that says something like: \n   %s\n   it means your csv is returning a TEXT type, not Number.  Maybe you have non-numerics mixed in, like commas or percent signs...?' %"--> unsupported operand type(s) for +: 'int' and 'str' <--")

    barcount = float(len(data.dfy.columns))
    barwidth = 1.00 / barcount

    fig, ax = plt.subplots()
    data.dfmain.plot.bar(x=data.dfx.columns[0], y=data.dfy.columns)
    ### ========== END CHART-SPECIFIC CODE ========== ###

    plt = coaVizLib.Postwork(log, arg, data, plt)

except Exception as e:
    msg = 'ERROR OCCURED DURING CHART GENERATION of file: %s\n%s' %(str(arg.pngfilepath), str(e))
    if len(data.dfmain)==0:
        msg = msg + '\n\nNOTE: DataFrame ("%s") contained no data, maybe you want to check that out.\n\n' %str(arg.csvfilepath)
    msg = msg + '\nFinal argument list, for your reading pleasure\n  (for more detail, see log file: "%s"):\n\n%s' %(coaLog.logfilename, arg.dictdisplay(arg.__dict__))

    log.error(msg)
    coaVizLib.make_empty_chart(str(arg.pngfilepath), msg)
finally:
    sys.exit(0)
