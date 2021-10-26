from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging, sys, pandas as pd, time, json, numpy
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter



def getJsonFilePath( filepathstring:str ) -> Path:
    return Path(Path(filepathstring).parent / 'coaVizConfig.json')

def byte_format(num, pos=0):
    return coa_format(num, pos, ['', 'K', 'M', 'G', 'T', 'P'])

def num_format(num, pos=0):
    return coa_format(num, pos)

def coa_format(num, pos, maglist=['', 'K', 'M', 'B', 'T', 'Q']):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.00
    return '%.1f%s' % (num, maglist[magnitude])


def Prework(log, arg, data):
    """perform all common PREWORK to generate coaVisualizations"""

    log.info('Performing Prework for coaViz processes: %s' %arg.title)
    formatter = FuncFormatter(byte_format) if arg.ynumberformat == 'byte' else FuncFormatter(num_format)
    plt.rcParams["figure.figsize"] = arg.width, arg.height
    plt.title(arg.title, fontsize=16, pad=20, color='grey')
    plt.xticks(fontsize = arg.xticksize, rotation = arg.xrotate, color='grey')
    xlabel = data.dfx.iloc[:,0].name if arg.xlabel == '<<column name>>' else arg.xlabel
    plt.xlabel(xlabel, fontsize = arg.labelsize, color='grey')
    plt.ylabel(arg.ylabel, loc = "top", fontsize = arg.labelsize, color='grey')
    plt.tick_params(axis='y', colors='grey')
    plt.gca().yaxis.grid(True) # turn on yaxis vertical lines
    log.debug('Prework Complete!')
    return plt


def Postwork(log, arg, data, plt):
    """perform all common POSTWORK to generate coaVisualizations"""

    log.info('Performing POSTWORK for coaViz processes: %s' %arg.title)

    # turn off borders, set xaxis items to grey
    log.debug('turning off spines (box around graph)')
    ax = plt.gca()
    ax.spines['right'].set_visible(arg.border)
    ax.spines['left'].set_visible( arg.border)
    ax.spines['top'].set_visible(  arg.border)
    ax.spines['bottom'].set_color('gray')
    ax.tick_params(axis='x', colors='grey')

    # toggle LOGSCALE
    ax.set_ylim(ymin = arg.ymin)
    if arg.logscale:
        log.debug('setting y axis scale to LOG')
        ax.set_yscale('log')
        if arg.ymin == 0: ax.set_ylim(ymin = 0.1 if arg.ymin==0 else arg.ymin )

    # hide some xaxis label, if too many dates to display properly  (set with variable: "xlabelflex" )
    x = 0 if arg.xlabelflex==0 else int(len(data.dfx) / arg.width / (8/arg.xticksize) / (4 * arg.xlabelflex))
    i = 0
    if x > 1:
        log.debug('hiding every %i of the xlabels, to prevent over-crowding' %x)
        for label in plt.gca().xaxis.get_ticklabels():
            label.set_visible(i%x==0)
            i+=1

    # apply any x/y label slice logic:
    log.debug('xlabelslicer: %s' %str(arg.xlabelslicer))
    if arg.xlabelslicer != [0,0]:
        s1 = None if arg.xlabelslicer[0] == 0 else int(arg.xlabelslicer[0])
        s2 = None if (len(arg.xlabelslicer)<2 or arg.xlabelslicer[1] == 0) else int(arg.xlabelslicer[1])
        s3 = None if (len(arg.xlabelslicer)<3 or arg.xlabelslicer[2] == 0) else int(arg.xlabelslicer[2])
        log.debug('slicing xlabel by positions: %s, %s' %(str(s1), str(s2)))
        new_labels = [i.get_text().strip()[s1:s2:s3] for i in plt.gca().xaxis.get_ticklabels()]
        plt.gca().xaxis.set_ticklabels(new_labels)

    # set legend if called for
    if arg.legendxy != (0,0):
        log.debug('drawing legend')
        plt.legend(loc = 'center', bbox_to_anchor = arg.legendxy, ncol = arg.legendcolumns)

    log.info('saving file: %s' %arg.pngfilepath)
    plt.savefig(arg.pngfilepath, transparent=True,bbox_inches='tight')

    return plt


def make_empty_chart(filepath:Path, msg:str = ''):
    """create an empty graph, with optional words written. Mostly aimed at creating a file during errors."""
    import matplotlib.pyplot as plt
    fig= plt.figure()
    fig.set_figheight(12)
    fig.set_figwidth(16)
    ax = fig.add_subplot()
    ax.text(0.01, 0.1, msg, fontfamily='Courier')
    fig.savefig(filepath)




@dataclass
class coaLog():
    """Class for setting up logging as needed for coaVizLib."""

    log: logging = logging.getLogger(__name__)
    logformat: logging.Formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:  %(message)s')
    logHandlers: dict = None
    timestamp: str = ''

    def __init__(self, standard_setups:str = 'default'):
        self.timestamp = ts = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.logHandlers = {}
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        self.log.handlers.clear()
        if standard_setups.lower()[:1] == 'd':  # debug
            self.addhandler('stream out to commandline', 'i')
            self.addhandler('program debug log', 'd', Path('coaViz.log'))
        if standard_setups.lower()[:1] == 's':   self.addhandler('stream out to commandline', 's')
        if standard_setups.lower()[:1] in ['4']: self.addhandler('stream out to commandline', 'd')
        if standard_setups.lower()[:1] in ['3']: self.addhandler('stream out to commandline', 'i')
        if standard_setups.lower()[:1] in ['2']: self.addhandler('stream out to commandline', 'w')
        if standard_setups.lower()[:1] in ['1']: self.addhandler('stream out to commandline', 'e')
        if standard_setups.lower()[:1] in ['n','0']: pass

    def __getloglevel__(self, loglevel) -> None:
        rtn = 0
        if loglevel[:1].lower() == 'd': rtn = logging.DEBUG
        if loglevel[:1].lower() == 'i': rtn = logging.INFO
        if loglevel[:1].lower() == 'w': rtn = logging.WARNING
        if loglevel[:1].lower() == 'e': rtn = logging.ERROR
        if rtn == 0: rtn = logging.INFO
        return rtn

    def clearhandlers(self) -> None:
        self.log.handlers.clear()
        return None

    def addhandler(self, name:str = '', loglevel:str='i', logfilepath:str='' ) -> logging.FileHandler:
        hname = logfilepath if name == '' else name
        hlvl = self.__getloglevel__(loglevel)
        ts = self.timestamp
        hlogfilepath = str(logfilepath).replace(r'{time}', ts).replace(r'{ts}', ts).replace(r'{timestamp}', ts)
        self.logfilename = hlogfilepath

        if hlogfilepath == '':
            handler = logging.StreamHandler()
            htype = 'streaming'
        else:
            handler = logging.FileHandler(hlogfilepath, 'w+')
            htype = 'file'

        handler.setFormatter(self.logformat)
        handler.setLevel(hlvl)
        self.log.addHandler(handler)
        self.logHandlers[hname] = handler
        return handler

@dataclass
class coaArg():
    """Class for turning the arg list into a coaViz dictionary, complete with default values to required keys."""

    log: object
    args: list
    args_unmapped: list
    jsonfilepath: str

    def __init__(self, log:object, args:object, configfilepath:Path = 'coaVizConfig.json'):
        self.log = log
        self.log.debug('coaArg class instatiated')
        self.jsonfilepath = configfilepath

        if not isinstance(args, list):
            self.log.error('variable provided: "args" is not a list.  Make sure your code looks something like this: \nimport sys\nv = coaArg(sys.argv)')
            raise TypeError

        self.reset(args, configfilepath)

    def contains(self, name:str) -> bool:
        return name in self.__dict__

    def reset(self, args:object, configfilepath:Path) -> None:
        self.args = args
        kwargs = self.digestArgs(args)
        configlist =  self.getconfig(configfilepath)
        kwargs = self.structurekwargs(kwargs, configlist)
        self.loadlocal(kwargs)
        self.log.info('Final argument list: \n%s' %self.dictdisplay(self.__dict__))


    def structurekwargs(self, kwargs:dict, configlist:list) -> dict:
        """Structures the kwargs according to the supplied list of entry configurations."""

        self.log.info('structuring keyword arguement dictionary to adhere to config definition (json)')
        for config in configlist:

            resolved = False
            if config['name'] in kwargs:
                self.log.debug('%s - found in kwargs dictionary, conforming type...' %str(config['name']))
                kwargs[config['name']] = self.applytype(kwargs[config['name']], config['type'], config['default'])
                resolved = True
            else:  #not found:
                self.log.debug('%s - missing from kwargs dictionary, seeking alias/default value...' %str(config['name']))

                # look for an alias
                for alias in config['aliases']:
                    if alias in kwargs and kwargs[alias] is not None:
                        self.log.debug('  found viable alias: %s' %alias )
                        kwargs[config['name']] = self.applytype(kwargs[alias], config['type'], config['default'])
                        resolved = True
                        break

                # if still missing, add as default
                if not resolved:


                    if config['default'][:2] == '<<' and config['default'][-2:] == '>>':  # special handling
                        self.log.debug('  default <<special handling>> detected: %s' %config['default'])

                        if ':replace(' in config['default']:  ### handle replace function:
                            self.log.debug('  processing special handling: "Replace"')
                            argname = config['default'].replace('<','').split(':')[0]
                            findstr = config['default'].split(':')[1].split("(")[1]
                            rplcstr = config['default'].split(':')[2].split(")")[0]
                            self.log.debug('  setting kwarg: %s = str(%s).replace("%s", "%s")' %(config['name'], str(argname), findstr, rplcstr))
                            kwargs[config['name']] = str(kwargs[argname]).replace(findstr, rplcstr)

                        elif config['default'].lower() == '<<no default>>':  ## means there is no default, error if missing
                            msg = 'this parameter has NO DEFAULT and is REQUIRED to continue.  Ensure a viable value for %s' %config['name']
                            self.log.error(msg)
                            raise ValueError(msg)

                        elif config['default'].lower() == '<<none>>':  ## replace with None type / aka empty / aka Null
                            self.log.debug('  default set as None, so returning None, aka Null, aka Nothing')
                            kwargs[config['name']] = None

                        else:  ### all other commands, simply leave <<comment>> in place:
                            kwargs[config['name']] = str(config['default'])
                            self.log.debug('  Unknown or down-stream handled <<special handling>>, continuing...')

                    else:  # not special handling, just add the default supplied, as-is
                        kwargs[config['name']] = self.applytype(config['default'], config['type'])
                        self.log.debug('no value supplied, using default value: %s' %str(kwargs[config['name']]))

        # special handling for legendxy:
        if 'legendx' in kwargs:
            self.log.debug('final special update to replace X value in legendxy(%s) with legendx(%s)' %(kwargs['legendxy'], kwargs['legendx']))
            kwargs['legendxy'] = ( self.applytype(kwargs['legendx'], 'float', '0.5'), kwargs['legendxy'][1] )
        if 'legendy' in kwargs:
            self.log.debug('final special update to replace Y value in legendxy(%s) with legendy(%s)' %(kwargs['legendxy'], kwargs['legendy']))
            kwargs['legendxy'] = ( kwargs['legendxy'][0], self.applytype(kwargs['legendy'], 'float', '-0.3') )

        # self.pngfilepath = str(Path(Path(os.getcwd()) / self.pngfilepath))

        return kwargs


    def applytype(self, val:str, finaltype:str, default:str=None) -> any:
        self.log.debug('applytype %s to value "%s"' %(finaltype, val))
        val = str(val).strip()
        if val=='<<none>>': val = None
        s2l = self.__str2list__
        try:
            if finaltype == 'str':        return str(val)
            if finaltype == 'int':        return (None if val==None else int(val))
            if finaltype == 'bool':       return (False if str(val).strip().lower()[:1] in ['f','0'] else True)
            if finaltype == 'float':      return float(val)
            if finaltype == 'list':       return list(s2l(val))
            if finaltype == 'list-int':   return list(map(int, s2l(val) ))
            if finaltype == 'list-float': return list(map(float, s2l(val) ))
            if finaltype == 'tuple':      return tuple(s2l(val))
            if finaltype == 'tuple-int':  return tuple(map(int, s2l(val)))
            if finaltype == 'tuple-float':return tuple(map(float, s2l(val)))
            if finaltype == 'dict':       return json.load(val)
        except ValueError as ex:
            self.log.exception('failed type conversion during applytype(%s, %s)' %(str(val),str(finaltype)))

        self.log.error('provided an unsupported type to convert: applytype(%s, %s)' %(str(val),str(finaltype)))
        if default:
            self.log.error('retrying with supplied default value: %s' %default)
            return self.applytype(default, finaltype)
        return None

    def __str2list__(self, strlist:str) -> list:
        if strlist == '': return []
        rtn = strlist.strip()
        rtn = rtn[1:-1] if rtn[:1] in['[','('] and rtn[-1:] in[']',')']   else rtn
        rtn = list(rtn.split(','))
        return list(map(lambda s: s.strip() , rtn))


    def getconfig(self, configfilepath:Path) -> list:
        """load json config document for arg defaults and types"""
        self.log.debug('loading config file: %s' %configfilepath)
        try:
            with open(configfilepath, 'r') as f:
                filetext = f.read()
            self.configfile = json.loads(filetext)
        except FileNotFoundError as e:
            self.log.exception('File Not Found: %s' %configfilepath)
            self.configfile = {'defined_args':{}}
            raise e

        self.defined_args = self.configfile['defined_args']
        self.log.info('loaded defined_args from configfile %s,  found %i arg definition entries' %(configfilepath, len(self.defined_args)))
        msg = []
        for d in self.defined_args:
            msg.append(str(d))
        self.log.debug('default arg definitions: \n%s' %('\n'.join(msg)))
        return self.defined_args


    def loadlocal(self, kwargs:dict) -> None:
        """Merge keyword argument dictionary into the coaArg class as native properties, callable via coaArgs.Name"""
        self.log.debug('merging kwargs into class __dict__ object (thus becoming native properties)')
        for name, value in kwargs.items():
            self.__dict__[name] = value
        return None


    def digestArgs(self, args: list) -> dict:
        """Turns a list of commandline arguements into a dictionary of name:value pairs, using colon as delimiter."""
        kwargs = {}
        self.args_unmapped = []
        for arg in args:
            argary = arg.split(':')
            if len(argary) >1:  # has both sides of the : delimiter
                kwargs[argary[0]] = argary[1]
            else:
                self.args_unmapped.append(arg)
        self.log.info('variables digested: \n%s' %self.dictdisplay(kwargs))
        if len(self.args_unmapped) > 0:
            self.log.warning('there are also %i argument(s) that were not in the correct format, and ignored: \n %s' %(len(self.args_unmapped), str(self.args_unmapped)))
        return kwargs


    def dictdisplay(self, anydict: dict) -> str:
        """Turns a dictionary into a human-formatted string, for display purposes."""
        rtn = []
        for n,v in anydict.items():
            if n not in['configfile','defined_args','log']: rtn.append('%s : %s'  %(n.rjust(25), v))
        return '\n'.join(rtn)



@dataclass
class coaColor():
    log: object
    all_colors: list
    default_colors: list
    custom_colors: list
    all_colors: list
    used_colors: list
    unused_colors: list

    def __init__(self, log:object, custom_colors:list=[], configfilepath:Path = 'coaVizConfig.json'):
        self.log = log
        self.log.info('coaColor class instatiated')
        self.custom_colors = custom_colors
        self.default_colors = self.getdefaultcolors(configfilepath)
        self.used_colors = []
        self.unused_colors = []
        self.__rebuild_lists__()
        self.log.debug(self.__str__())

    def __rebuild_lists__(self) -> None:
        self.log.debug('rebuilding color lists')
        self.all_colors = self.custom_colors.copy()
        self.all_colors.extend(self.default_colors)
        self.unused_colors = self.all_colors.copy()
        for color in self.used_colors:
            self.unused_colors.remove(color)
        return None

    def getdefaultcolors(self, configfilepath:Path) -> list:
        self.log.debug('loading config file: %s' %configfilepath)
        try:
            with open(configfilepath, 'r') as f:
                config = json.loads(f.read())
        except FileNotFoundError as e:
            self.log.exception('File Not Found: %s' %configfilepath)
            raise e

        rtn = list(config['default_colors'])
        self.log.info('default colors loaded from file: %s' %rtn)
        return rtn

    def reset(self) -> None:
        """Resets all color dictionaries back to initial state, including resetting used and unused states."""
        self.log.warning('resetting all colors back to original state, including used/unused status')
        self.used_colors = []
        self.__rebuild_lists__()
        return None

    def getnextcolor(self) -> str:
        if len(self.unused_colors) == 0:
            self.log.error('THE LIST OF AVAILABLE COLORS HAS BEEN EXPENDED.  TO PREVENT ERRORS, WILL NOW RESET LIST AND BEGIN RE-USING COLORS. TO AVOID THIS ERROR IN THE FUTURE, PLEASE ADD MORE CUSTOM COLORS TO THE coaColors CLASS.')
            self.reset()
        rtn = self.unused_colors.pop(0)
        self.used_colors.append(rtn)
        self.log.debug('getnextcolor has returned %s  (%i unused colors remaining)' %(rtn, len(self.unused_colors)))
        return rtn

    def getnextcolors(self, colors_to_get:int) -> list:
        """Returns list of N colors"""
        rtn = []
        for i in range(0,colors_to_get):
            rtn.append( self.getnextcolor() )
        self.log.debug('getnextcolors has returned list of %i colors: %s' %(colors_to_get, str(rtn)))
        return rtn

    def addcolor(self, new_color = '') -> list:
        """Adds a new color to the end of our custom_color list.  This does NOT append to or reset_unused_colors()."""
        self.log.info('add new color to custom_colors: %s' %new_color)
        self.custom_colors.append(new_color)
        self.__rebuild_lists__()
        return self.custom_colors

    def addcolors(self, new_colors = []) -> list:
        """Adds a list of new colors to the end of our custom_color list.  This does NOT append to or reset_unused_colors()."""
        self.log.info('add new colors to custom_colors: %s' %new_colors)
        self.custom_colors.extend(new_colors)
        self.__rebuild_lists__()
        return self.custom_colors

    def __str__(self) ->str:
        rtn = ['current color status:']
        rtn.append('%i custom colors (used first):\n%s' %(len(self.custom_colors), str(self.custom_colors)))
        rtn.append('%i default colors (used second):\n%s' %(len(self.default_colors), str(self.default_colors)))
        rtn.append('%i ALL colors (total defined):\n%s' %(len(self.all_colors), str(self.all_colors)))
        rtn.append('%i used colors (previously consumed colors):\n%s' %(len(self.used_colors), str(self.used_colors)))
        rtn.append('%i unused colors (remaining unused colors):\n%s' %(len(self.unused_colors), str(self.unused_colors)))
        return '\n'.join(rtn)

    def addcolors_to_dataframe(self, df:pd.DataFrame, override:str = '') -> pd.DataFrame:
        """Add color attribute to each series, honoring column-defined color codes ("name--#000000") as priority.
        If the column-defined color code does not exist, take the next available color."""
        self.log.debug('add color attribute to each DataFrame.Series object')

        # build names and colors dictionaries, per column in df
        names = {}
        colors = {}
        for col in df.columns:
            if '--' in col:
                names[col] = col.split('--')[0]
                colors[names[col]] = col.split('--')[1] if override == '' else override
                self.log.debug('color code found in column name - \n\torigional=%s\n\tname = %s\n\tcolor = %s%s' %(col,names[col], colors[names[col]], str(' (overridden by call)' if override else '')))
            else:
                names[col] = col
                colors[names[col]] = self.getnextcolor() if override == '' else override
                self.log.debug('color %s: \n\tname = %s\n\tcolor = %s' %( str('overridden by call' if override else 'assigned from usused pool'), names[col], colors[names[col]]))

        # rename all columns
        df = df.rename(columns=names)

        # add color to each series
        for col in df.columns:
            series = df.loc[:,col]
            series.__class__ = coaSeries  ### subclass the Series to add Color
            series.color = colors[col]
        return df

    def getcolormap(self, df:pd.DataFrame, override:str = '') -> dict:
        """Build a map dictionary between dataframe, series/column, and the color attribute, honoring column-defined color codes ("name--#000000") as priority.
        If the column-defined color code does not exist, take the next available color."""
        self.log.debug('build color map for each dataframe.series')

        # build names and colors dictionaries, per column in df
        names = {}
        colors = {}
        for col in df.columns:
            if '--' in str(col):
                names[col] = str(col).split('--')[0]
                colors[names[col]] = col.split('--')[1] if override == '' else override
                self.log.debug('color code found in column name - \n\toriginal=%s\n\tname = %s\n\tcolor = %s%s' %(col,names[col], colors[names[col]], str(' (overridden by call)' if override else '')))
            else:
                names[col] = col
                colors[names[col]] = self.getnextcolor() if override == '' else override
                self.log.debug('color %s: \n\tname = %s\n\tcolor = %s' %( str('overridden by call' if override else 'assigned from usused pool'), names[col], colors[names[col]]))

        # rename all columns
        df = df.rename(columns=names)

        # build final color map
        colormap = {}
        for col in df.columns:
            colormap[col] = colors[col]
        return df, colormap



@dataclass
class coaData():
    """Class for turning CSV files into dataframes for visualization processing."""

    log: object
    colors: object
    args: object
    dfy: pd.DataFrame
    dfx: pd.DataFrame
    dfmain: pd.DataFrame


    def __init__(self, log:object, args:object=None):
        self.log = log
        log.debug('coaData class instatiated')
        self.args = args
        self.colors = coaColor(log, self.args.colors, args.jsonfilepath)
        self.loadCSV(self.args.csvfilepath, self.args.xcolumns, self.args.ycolumns)


    def loadCSV(self, csvfilepath:Path, xcolumns:list=[0], ycolumns:list=[]) -> None:
        """Load csv file content into several data frames, per use"""

        if csvfilepath == '':
            self.log.error('CANNOT LOAD CSV WITHOUT csvfilepath OF CSV FILE.  SERIOUSLY.')
            raise Exception

        # open data into dataframe
        self.log.info('loading data into dataframes from file: %s' %csvfilepath)
        df = pd.read_csv(csvfilepath)
        self.log.info('data file loaded to "dfmain" with %i columns and %i rows' %(len(df.columns),len(df)))
        if len(df)==0:
            msg = '\n%s\nDATAFRAME HAD NO ROWS... this is likely to end poorly.\n%s' %('-'*50, '_'*50)
            self.log.error(msg)

        # assign default column positions, if missing
        if ycolumns == []: ycolumns = list(set([x for x in range(len(df.columns))]) - set(xcolumns)) # default: all columns not in xcolumns
        if xcolumns == []: xcolumns = [0]  # defaults to first column

        # pivot, if requested
        if self.args.dfpivot:
            df = self.autopivot(df, xcolumns, ycolumns)
            ycolumns = list(set([x for x in range(len(df.columns))]) - set(xcolumns)) # reset ycolumns to all non-xcolumns

        # assign xcolumnnames and ycolumnnames lists
        self.args.ycolumns = ycolumns
        self.args.xcolumnnames = self.build_columnnames(df, xcolumns)
        self.args.ycolumnnames = self.build_columnnames(df, ycolumns)

        # SORT if specified
        sortcol = int(self.args.sort[0] if len(self.args.sort) >= 1 else -1)
        sortasc = bool('asc' in str(self.args.sort[1]) if len(self.args.sort) >= 2 else 'desc')
        self.log.debug('sorting requirements: sort? %s   column: %i, %s' %(str(sortcol>0), sortcol, sortasc))

        if str(sortcol)[-2:] == '99':  # special: sort rows by aggregate of all columns
            self.log.debug('special sorting requested: sum of all ycolumns')
            df['sortcol_sumall'] = df.iloc[:, ycolumns ].sum(axis=1)
            sortcol = len(df.columns)-1

        if sortcol >= 0:
            self.log.debug('sorting specified, col: %i, asc: %s' %(sortcol, str(sortasc)))
            df.sort_values(by = df.iloc[:, sortcol].name, ascending = sortasc, inplace=True)
            self.log.debug('sorting complete')
        if 'sortcol_sumall' in df.columns:  df.drop('sortcol_sumall', axis=1, inplace=True)


        # save dataframes to class objects
        self.colormap = {}

        self.dfy, self.colormap['dfy'] = self.colors.getcolormap(df.iloc[:, ycolumns])
        self.log.info('Y axis dataframe "dfy" created containing fields: %s' %str(list(self.dfy.columns)))

        self.dfx, self.colormap['dfx'] = self.colors.getcolormap(df.iloc[:, xcolumns])
        self.log.info('X axis dataframe "dfx" created containing fields: %s' %str(list(self.dfx.columns)))

        self.dfmain, self.colormap['dfmain'] = self.colors.getcolormap(df, '#000000')
        self.log.info('full dataframe "dfmain" created containing fields: %s' %str(list(self.dfmain.columns)))

        #self.args.ymax = self.dfy.iloc[:,].max().max()
        #self.args.ymin = self.dfy.iloc[:,].min().min()

        return None


    def autosort(self):
        pass

    def autopivot(self, df:pd.DataFrame, xcolumns:list, ycolumns:list, aggfunction:callable = numpy.sum) -> pd.DataFrame:
        if len(ycolumns) != 2:
            self.log.error('autopivot requires ycolumn to supply exactly 2 column indexes (in order): Column to Pivot into New Columns, Data Values (aggregated)')
            return df
        if len(xcolumns) != 1:
            self.log.error('autopivot requires xcolumn to supply exactly 1 column index: Column Containing Unique Row Values')
            return df
        colname_unique_rowindex = df.iloc[:, xcolumns[0]].name
        colname_columnvalue = df.iloc[:, ycolumns[0]].name
        colname_data = df.iloc[:, ycolumns[1]].name
        collist = [colname_unique_rowindex] + list(df.loc[:,colname_columnvalue].unique())  # record the original list order, to reset at the end

        self.log.info('performing pivot operation on dataframe:\nColumn for Unique Row /Index: %s\nColumn to Pivot to New Columns: %s\nData Column: %s\nFunction: %s' %(colname_unique_rowindex, colname_columnvalue, colname_data, str(aggfunction)))
        rtndf = pd.DataFrame( pd.pivot_table(df, index = colname_unique_rowindex, columns = colname_columnvalue, values = colname_data, aggfunc=aggfunction)).reset_index()
        rtndf = rtndf[collist]
        return rtndf



    def build_columnnames(self, df:pd.DataFrame, columns:list) -> list:
        """build a x or y columnnames list given a list of column indexes and dataframe"""

        if len(df.columns) < max(columns):
            msg = 'max from supplied list of column indexes is higher than the total number of columns in the dataframe... aka this aint going to work.\ncolumns: %s\ndataframe.columns: %s' %(columns, df.columns)
            self.log.error(msg)
        try:
            columnnames = []
            for icol in columns:
                columnnames.append( df.iloc[:,icol].name )
        except Exception as ex:
            self.log.exception('Error while translating column indexes into column names:')
        return columnnames
