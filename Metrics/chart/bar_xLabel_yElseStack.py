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

    # iterate thru all columns in dfY and iterate / generate bar data:
    bottom = [0 for z in data.dfy.iloc[:,0]]
    for itr, col in enumerate(data.dfy.columns):
        ydata = list(data.dfy.loc[:,col])
        plt.bar(data.dfx.iloc[:,0],
                 ydata,
                 label = data.dfy.loc[:,col].name,
                 color = data.colormap['dfy'][col],
                 zorder = int(1/(itr+1)*100),
                 linestyle = '-',
                 linewidth = 2,
                 bottom = bottom)
        bottom = [a + b for a,b in zip(bottom, ydata)]

    ### ========== END CHART-SPECIFIC CODE ========== ###


    plt = coaVizLib.Postwork(log, arg, data, plt)

except Exception as ex:
    log.exception('ERROR OCCURED DURING CHART GENERATION, SKIPPING...')
