import logging, sys
from datetime import datetime
from tkinter import EXCEPTION 
# from .sj_logger import sj_Logger

print(f'loaded {__name__}')

# Misc helper functions


class sj_Misc():

    def __init__(self, log=None) -> None:
        if log:
            self.log = log
        else:
            #Creating and Configuring Logger
            logging.basicConfig(stream = sys.stdout, 
                                format =  "%(asctime)s %(levelname)s - %(message)s", 
                                level = logging.DEBUG)
            self.log = logging.getLogger()


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

    def parse_namevalue_args(self, args:list, nvdelim:str=':', defaults={}, first_item_name:str='scriptfilepath') -> dict:
        """Parse list of argments and split into dictionary based on delimiter. Both name/values are trimmed, to remove leading/trailing white-space.
        If delimiter is not found for a list item, that item is added as the dict name(key), and the value is left as None.
        For example, passing in the list (with default delim):
            [  'dog :fluffy',   'cat: spikey',   ' fish']       will result in a dict of:
            {  'dog' : 'fluffy',  'cat' : 'spikey',  'fish' : None} 
 
        Args:
            args (list): list of arguments.
            nvdelim (str, optional): delimiter used for splitting items into name:value as dict entries. Defaults to ':'.
            first_item_name (str, optional): name of the first list item supplied, if name is not supplied (expecting sys.argv[0]). Defaults to 'scriptpath'.
            defaults (dict): dict of defaulted items to include, if missing.  Defaults to empty dict.

        Returns:
            dict: parsed dict of argments from list passed in.
        """
        rtn = {}
        try:
            self.log.info(f'parsing argument list with delimiter   {nvdelim}')
            # for each arg in list, 
            for i, arg in enumerate(args):
                argname = str(arg.split(nvdelim)[0]).strip()  # define argument name as: first string split by delim
                argval = str(arg).replace(argname,"").strip() # define argument value as: everything that's not argname (regardless how many other delims)
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

            

    def translate_simple_dateformat(self, input_dateformat:str) -> str:
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
        oldfmt = oldfmt.replace('12hh','ii').replace('12h','i').replace('24h','h').replace('excel','m/d/yy i:m:s p').lower()
        charlist = []
        date_markers = ['y','d','/','-','w']
        time_markers = ['h','s',':','i','p','a']
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
        self.log.debug(f'Translating date format from:  {input_dateformat.ljust(20," ")}  to:  {rtn.ljust(25," ")}   aka:  { datetime.now().strftime(rtn) }')
        return rtn




if __name__ == '__main__':

    misc = sj_Misc()
    
    for fmt in ['m/d/yy h:m:s', 'yyyy-mm-dd hh:mm:ss', 'mm/dd/yyyy', 'hh:mm:ss', 'yyyymmdd_hhmmss', 'Excel', '24hh == 12hhp']:
        oldfmt = fmt.rjust(20,' ')
        newfmt = misc.translate_simple_dateformat(fmt)
        nowish = datetime.now()
        # print(f'from {oldfmt}   to   {newfmt.ljust(25," ")}  looks like { nowish.strftime(newfmt)}')

