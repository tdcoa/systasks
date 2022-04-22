from email import iterators
import enum
import logging, re, fnmatch, sys, pprint
from pathlib import Path
from datetime import datetime
from tkinter import EXCEPTION
from typing import Iterable
from xml.dom import NotFoundErr 
# from .sj_logger import sj_Logger

version = 'v1.2'
print(f'loaded {__name__} { version }')

# Misc helper functions


class sj_Misc():
    log: logging.Logger = None
    logfilepath:Path = None
    tokens: dict 

    def __init__(self, log=None, logfilepath=None) -> None:
        self.tokens = {'version':version}
        if log:
            self.logfilepath = ''
            self.log = log 
        else:
            if logfilepath:
                self.logfilepath = logfilepath
                self.log = self.get_logger(logfilepath)

        

    @property
    def time_tokens(self) ->dict:
        return { '12hh'     : 'ii'
                ,'12h'      : 'i'
                ,'24h'      : 'h'
                ,'excel'    : 'm/d/yy i:m:s p'
                ,'tddate'   : 'yyyy-mm-dd'
                ,'tdtime'   : 'yyyy-mm-dd hh:mm:ss'
                ,'logtime'  : 'yyyymmdd_hhmmss'
                ,'logfile'  : 'yyyymmdd_hhmmss'
                ,'logdate'  : 'yyyymmdd'
                ,'timestamp': 'yyyy-mm-dd hh:mm:ss'
                ,'date'     : 'yyyy-mm-dd'
                ,'time'     : 'hh:mm:ss' 
                ,' AM'      : ' a'
                ,' PM'      : ' p'
                }


    def get_logger(self, logfilepath=None) -> logging.Logger:
        """Builds and returns a simple logger object, with optional file output.
        This is a simple convenience function that makes consistent some logging characteristics.

        Args:
            logfilepath (_type_, optional): If set as a filepath, will create and log to set file. 
                                            Defaults to None / not logged to file.

        Returns:
            logging.Logger: new logging object
        """
        try:
            if logfilepath:    
                logfilepath = Path(self.replace_tokens(logfilepath)).resolve()
                logfilepath.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(handlers=[  logging.FileHandler(filename = logfilepath),
                                            logging.StreamHandler()],
                                format =  "%(asctime)s %(levelname)-8s %(funcName)s:  %(message)s", 
                                level = logging.DEBUG)

            log = logging.getLogger()
            log.setLevel(logging.DEBUG)
        except Exception as ex:
            logging.basicConfig()
            log = logging.getLogger()
            log.exception(f"Exception when adding file to logger: { str(logfilepath) }\n{ ex }\n\nIgnoring Error and Continuing...")
            
        return log


    @staticmethod
    def globi(search_path:Path, glob_pattern:str, case_sensitive:bool = True) -> list:
        """Regular expressions glob function - applies regex pattern match to Path directory and return matching names.

        Args:
            
            search_path (Path): Path object to search within if directory, if Path is a file search is moved to the Path.parent directory.
            glob_pattern (str): Regex pattern string
            case_sensitive (bool): Indicate whether glob should be case sensitive (true) or not (false).

        Returns:
            _type_: List of matching files/dir as Path objects.
        """
        reobj = re.compile( fnmatch.translate(glob_pattern)) if case_sensitive else re.compile( fnmatch.translate(glob_pattern), re.IGNORECASE)
        if search_path.is_file(): search_path = search_path.parent
        rtn = [Path(pth).resolve() for pth in search_path.iterdir() if reobj.match(str(pth))]
        return rtn
 
 
    @staticmethod
    def globre(searchpath:Path, pattern:str) -> list:
        return  re.compile( fnmatch.translate(pattern), re.IGNORECASE)


    @staticmethod
    def isfloat(strnumber:str) ->bool:
        """Tests whether a string-numeric can be converted to a float.

        Args:
            strnumber (str): string-formatted number candidate.

        Returns:
            bool: Whether the string-candidate can be translated to a float()
        """
        try:
            float(strnumber)
            return True 
        except ValueError:
            return False 


    def replace_tokens(self, source:str, token_replace_dict:dict={}) ->str:
        """Replaces all {tokens} found in supplied string with any token found in 
        the supplied token_replace_dict, replacing {name} with the supplied dict value. 
        If the token is not found in the supplied dict, it will look at the class 
        self.token dictionary, and failing that, if the token is_time_token(), it will be 
        replaced with the formatted time string via nowish(token).  
        If no token is found in any of those sources, then the token itself is 
        used, minus the {} wrapper.

        Args:
            source (str): Original source string containing {tokens}.
            token_replace_dict (dict, optional): Dictionary containing name/value pairs for replacement. Defaults to {}.

        Returns:
            str: Token-replaced version of input: source
        """
        p1 = p2 = s1 = 0
        part = []
        while True:
            p1 = source.find('{', s1)
            p2 = source.find('}', p1)
            if p1 <= 0 or p2 <= 0: 
                part.append(source[s1:])
                break 

            part.append(source[s1:p1]) # save everything before first { delimiter
            replace_token = source[p1+1:p2] # identify and replace token

            if replace_token in list(token_replace_dict.keys()):  # is in supplied dict?
                replace_token = token_replace_dict[replace_token]
            elif replace_token in list(self.tokens.keys()):  # is in class token dict?
                replace_token = self.tokens[replace_token]
            elif self.is_time_token(replace_token):   # looks like a time token?
                replace_token = self.nowish(replace_token)

            part.append(replace_token)  # save the final replace_token 
            s1 = p2+1
        return ''.join(part)
        

            

                    
    def is_time_token(self, token:str) -> bool:
        """Tests supplied token (string) and returns True if it maps to an expected simplified time format.
        Note, this doesn't mean the supplied token won't work as a simplifed time format, only that it 
        cannot be explicitly determined to be a time token.

        Args:
            token (str): any string to test.

        Returns:
            bool: is the string supplied a valid time token?
        """
        # first check for standard abbreviations:
        istime = token in list(self.time_tokens.keys())
        
        if not istime: 
            # look for characters that would disqualify the string as a time token
            istime = True # seek to disprove:
            for c in token:
                if c not in ['y','d','/','-','w','h','s',':','i','p','a','m',' ']:
                    istime = False
                    break 
        return istime 

        

    def nowish(self, datetime_format:str='yyyy-mm-dd_hhmmss') ->str:
        return datetime.now().strftime( self.translate_simple_dateformat(datetime_format) )


    def remove_extra_spaces(self, string:str) -> str:
        """reduces all extra spaces inside a string to a single space

        Args:
            string (str): any string value

        Returns:
            str: string value with multiple spaces replaced with a single space
        """
        while True:
            if '  ' in string: 
                string = string.replace('  ',' ')
            else:
                break
        return string.strip()

    def parse_namevalue_args(self, args:list, nvdelim:str=':', defaults={}, required=[], first_item_name:str='scriptfilepath') -> dict:
        """Parse list of argments and split into dictionary based on delimiter. Both name/values are trimmed, to remove leading/trailing white-space.
        If delimiter is not found for a list item, that item is added as the dict name(key), and the value is left as None.
        For example, passing in the list (with default delim):
            [  'dog :fluffy',   'cat: spikey',   ' fish']       will result in a dict of:
            {  'dog' : 'fluffy',  'cat' : 'spikey',  'fish' : None} 
 
        Args:
            args (list): list of arguments.
            nvdelim (str, optional): delimiter used for splitting items into name:value as dict entries. Defaults to ':'.
            defaults (dict): dict of defaulted items to include, if missing.  Defaults to empty dict.
            required (list): list of required names in the list, and will throw error if not found.  Defaults to empty list.
            first_item_name (str, optional): name of the first list item supplied, if not supplied (expecting sys.argv[0]). Defaults to 'scriptfilepath'.
            

        Returns:
            dict: parsed dict of argments from list passed in.
        """
        rtn = {}
        try:
            self.log.info(f'parsing argument list with delimiter   {nvdelim}')
            # for each arg in list, 
            for i, arg in enumerate(args):
                argname = str(arg.split(nvdelim)[0]).strip()  # define argument name as: first string split by delim
                argval = str(arg[len(argname)+1:]).strip() # define argument value as: everything that's not argname (regardless how many other delims)
                if argval[:1]==nvdelim: argval = argval[1:].strip() # if argval is left starting with delimiter, clean up /remove
                if i==0 and argval=='' and len(first_item_name)>0:  # if arg[0] doesn't suppply delimiter, assign first_item_name (assumption is sys.argv[0]) 
                    argval = argname
                    argname = first_item_name.strip()
                rtn[argname] = argval if len(argval)>0 else None # add to return dict 
                self.log.debug(f'  added name:  {argname} == {rtn[argname]}')
            for n,v in defaults.items():  # add any missing defaults
                if n not in rtn:
                    self.log.debug(f'  added default:  {n} == {v}')
                    rtn[n] = v

            # with everything parsed out, test for required items and throw error if missing
            for rqd in required:
                if rqd not in list(rtn.keys()): raise NotFoundErr(f'Required argument not supplied: {rqd}')

        except Exception as ex:
            self.log.exception(f'ERROR IN sj_misc.parse_namevalue_args\n{ex}')
        return rtn 



    def dict_to_class(self, srcdict:dict) -> object:
        """Converts a dictionary into a class object.

        Args:
            srcdict (dict): dictionary to convert.

        Returns:
            object: class object with dict items translated to class properties.
        """
        class dict2class(): pass 
        rtn = dict2class()
        for n, v in srcdict.items():
            rtn.__setattr__(n,v)
        return rtn 

            
    def is_simple_date_format(self, input_date:str, input_dateformat:str) -> bool:
        try:
            tst = datetime.strptime(input_date, self.translate_simple_dateformat(input_dateformat))
            return True
        except: 
            return False

    def is_date_format(self, input_date:str, input_dateformat:str) -> bool:
        try:
            tst = datetime.strptime(input_date, input_dateformat)
            return True
        except: 
            return False



    def translate_simple_dateformat(self, input_dateformat:str, skip_log:bool=False) -> str:
        """Translates a simplified date format into python strftime format, for consumption in datetime.datetime. 
        Simplified format will look visually similar to the final output, and is useful for bridging between MSOffice and Python. 
        Also performs context-specific classification of shared characters, such as "m" for both month and minute.  
        For example, supplying  yyyy-mm-dd hh:mm:dd will work as expected, using the context of surrounding characters  
        to interpret between Month and Minute.  

        Args:
            input_dateformat (str): simplified format string (i.e.,  yyyy-mm-dd hh:mm:ss )

        Returns:
            str: format string compatible with datetime.datetime.strftime() functions
        """
        oldfmt = str(self.remove_extra_spaces(input_dateformat)).lower()
        for fmtfind, fmtreplace in self.time_tokens.items():
           oldfmt = oldfmt.replace(fmtfind, fmtreplace)
        charlist = []
        date_markers = ['y','d','/','-','w']
        time_markers = ['h','s',':','i','p','a','f']
        both_markers = ['m']

        # iterate each character of format, and assign a type (date/time/unknown)
        prev_chardict = {}
        repeat = 0
        for i, c in enumerate(oldfmt):  
            ctype = None 

            if c in date_markers: ctype = 'd'
            if c in time_markers: ctype = 't'
            if c in both_markers:  # use context of surrounding characters
                ctype = None 
                # Oscillate forward and backward until we find the next closest valid value:
                for o in range(1, len(oldfmt)):
                    at_beginning = bool(((i-o) < 0))
                    at_end = bool(i+o == len(oldfmt))
                    if not at_beginning: # look behind unless at beginning of string
                        oc = oldfmt[i+(o*-1): i+1+(o*-1)]
                        if oc in date_markers: ctype = 'd'
                        if oc in time_markers: ctype = 't'
                    if not ctype and not at_end:  # look ahead unless found, or at end of string
                        oc = oldfmt[i+o: i+1+o]
                        if oc in date_markers: ctype = 'd'
                        if oc in time_markers: ctype = 't'
                    if ctype: break 

            if not ctype: ctype = 'u'
            chardict = {'char':c, 'type':ctype}

            # track / collapse repeating characters
            if prev_chardict != {} and f'{chardict["char"]}--{chardict["type"]}' == f'{prev_chardict["char"]}--{prev_chardict["type"]}': 
                prev_chardict['repeat'] +=1
            else:
                chardict['repeat'] = 1
                charlist.append(chardict)
                prev_chardict = chardict 

        # final translation of characters into strftime format
        fmt = []
        for c in charlist:
            cd = ''
            if   c['type'] == 't':
                if   c['char'] == 'h': 
                    if   c['repeat'] ==1: cd = '%H' # %-H
                    elif c['repeat'] >=2: cd = '%H'
                elif c['char'] == 'i': 
                    if   c['repeat'] ==1: cd = '%I' # %-I
                    elif c['repeat'] >=2: cd = '%I'
                elif c['char'] == 'm': 
                    if   c['repeat'] ==1: cd = '%M' # %-M
                    elif c['repeat'] >=2: cd = '%M'
                elif c['char'] == 's': 
                    if   c['repeat'] ==1: cd = '%S' # %-S
                    elif c['repeat'] >=2: cd = '%S'
                elif c['char'] in ['a','p']: cd = '%p' # am/pm
                elif c['char'] == 'f':    cd = '%f' # fractional seconds

            elif c['type'] == 'd':
                if   c['char'] == 'y': 
                    if   c['repeat'] <=2: cd = '%y'
                    elif c['repeat'] >=3: cd = '%Y'
                elif c['char'] == 'm': 
                    if   c['repeat'] ==1: cd = '%m' # %-m 
                    elif c['repeat'] ==2: cd = '%m'
                    elif c['repeat'] ==3: cd = '%b'
                    elif c['repeat'] >=4: cd = '%B'
                elif c['char'] == 'w': 
                    if   c['repeat'] ==1: cd = '%w'
                    elif c['repeat'] ==2: cd = '0%w'
                    elif c['repeat'] >=3: cd = '%W'
                elif c['char'] == 'd': 
                    if   c['repeat'] ==1: cd = '%-d'
                    elif c['repeat'] ==2: cd = '%d'
                    elif c['repeat'] ==3: cd = '%a'
                    elif c['repeat'] >=4: cd = '%A'            
            if cd == '': 
                cd = str(c['char']) * int(c['repeat'])
            fmt.append(cd)
        
        rtn = ''.join(fmt).strip()
        if self.log and not skip_log:
            self.log.debug(f'Translating date format from:  {input_dateformat.ljust(20," ")}  to:  {rtn.ljust(25," ")}   aka:  { datetime.now().strftime(rtn) }')
        return rtn




if __name__ == '__main__':
    
    logfilepath = str(Path(sys.argv[0]).resolve().parent / 'logs' / '{logfile}_test_{version}.txt')
    misc = sj_Misc(logfilepath=logfilepath)

    if False:
        for fmt in ['m/d/yy h:m:s', 'logfile', 'tdtime', 'tddate', 'yyyy-mm-dd hh:mm:ss', 'mm/dd/yyyy', 'hh:mm:ss', 'yyyymmdd_hhmmss', 'Excel', '24hh == 12hhp']:
            oldfmt = fmt.rjust(20,' ')
            newfmt = misc.translate_simple_dateformat(fmt)
            nowish = datetime.now()
            # print(f'from {oldfmt}   to   {newfmt.ljust(25," ")}  looks like { nowish.strftime(newfmt)}')

        print( misc.replace_tokens('/some/path/toa/{yymmdd}_{subject}_{version}_{excel}.txt', {'subject':'poop','excel':'appname'}) )
        print( misc.replace_tokens('/some/path/toa/{logfile}_{subject}_{version}_{tddate}.txt at {excel}') )
        pprint.pprint(misc.time_tokens)


    for tm in ['3/3/2022', '3/3/22 4:15:00 p']:
        for fmt in ['mm/dd/yyyy hh:mm:ss p', 'mm/dd/yyyy hh:mm:ss']:
            print(misc.adjust_simple_dateformat(tm,fmt))


    print('done!')