import sys

class VisUtil():
    color_default=['#27C1BD','#31A354','#20A0FF','#E3C700','#E39000','#E400FF']
    color_cache = []
    color_gradient = 1
    csvfile = ''
    args = {}

    def __init__(self, *args):
        self.process_args(*args)
        self.color_cache = [c for c in self.color_default]

    def log(self, *args):
        print(*args)

    def process_args(self, *args):
        for arg in args:
            goodsyntax = False
            if ':' in arg:
                argobj = arg.split(':')
                if len(argobj) >1:
                    self.args[argobj[0]] = arg[len(argobj[0])+1:]
                    goodsyntax = True
            if not goodsyntax:
                self.log('Supplied arg not conformed to name:value syntax requirements:\t%s' %str(arg))
        # apply aliases
        if 'barlogscale' not in self.args and 'logscale' in self.args: self.args['barlogscale']=self.args['logscale']
        if 'yintercept' not in self.args and 'ymin' in self.args: self.args['yintercept']=self.args['ymin']
        if 'csvfile' not in self.args and 'file' in self.args:  self.args['csvfile']=self.args['file']
        # check for required
        if 'csvfile' not in self.args:
            raise Exception('Missing Required Argument: csvfile')
            return None
        # apply defaults
        if 'color_default'  in args: self.color_default = args['color_default']
        if 'color_gradient' in args: self.color_gradient = args['color_gradient']
        if 'title'    not in self.args: self.args['title'] = str(self.args['csvfile'].split('.')[0].split('--')[-1].replace('_',' ').upper())
        if 'height'   not in self.args: self.args['height'] = 6
        if 'width'    not in self.args: self.args['width'] = 12
        if 'save'     not in self.args: self.args['save'] = True
        if 'logscale' not in self.args: self.args['logscale'] = False
        # convenience shortcuts
        self.csvfile = self.args['csvfile']

    def reset_colors(self, **kwargs):
        cs = []
        if 'default' in kwargs: self.color_default = [c for c in kwargs['default']]
        if 'gradient' in kwargs: self.color_gradient = int(kwargs['gradient'])
        if 'add' in kwargs: cs = list(kwargs['add'])
        cs = cs + self.color_default
        cc = self.color_cache = []

        for c in cs:
            self.log('\nadding color: %s' %c)
            tint_count = int(self.color_gradient /2)
            normal = 1
            shade_count =  self.color_gradient - tint_count - normal
            self.log('tint: %i  normal: %i  shade: %i' %(tint_count, normal, shade_count))

            # add shades (darkest to lightest, so backwards)
            shades = []
            s = c
            for i in range(0,shade_count):
                s = self.shade(s)
                shades.append(s)
            for s in reversed(shades):
                cc.append(s)
                self.log('appending shade: %s' %s)

            # add base color
            cc.append(c)
            self.log('appending normal: %s' %c)

            # add tints (reverse so it goes light to dark)
            t = c
            for i in range(0,tint_count):
                t = self.tint(t)
                cc.append(t)
                self.log('appending tint: %s' %t)
        if cc==[]:  cc = [c for c in self.last_full_color_cache]
        self.color_cache = [c for c in cc]
        self.last_full_color_cache = [c for c in cc]
        return cc

    def next_color(self):
        if len(self.color_cache) ==0:  self.color_cache = [c for c in self.last_full_color_cache]
        return self.color_cache.pop(0)

    def all_colors(self):
        return self.last_full_color_cache


    @staticmethod
    def name_color(colname=''):
        if '--' in colname:
            name  = colname.split('--')[0]
            color = colname.split('--')[1].lower()
        else:
            name = colname
            color = ''
        return (name, color)

    @staticmethod
    def human_format(num, pos):
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.00
        return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

    @staticmethod
    def shade(hexvalue="", pct=0.25):
        """takes one hex color value and returns a shaded/darkened hex color value."""
        h = hexvalue[1:] if hexvalue[:1]=="#" else hexvalue[:6]
        [r,g,b] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return '#{:02x}{:02x}{:02x}'.format( int(r*(1-pct)), int(g*(1-pct)), int(b*(1-pct)) )

    @staticmethod
    def tint(hexvalue="", pct=0.25):
        """takes one hex color value and returns a tinted/lightened hex color value."""
        h = hexvalue[1:] if hexvalue[:1]=="#" else hexvalue[:6]
        [r,g,b] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return '#{:02x}{:02x}{:02x}'.format( int(r+((255-r)*pct)), int(g+((255-g)*pct)), int(b+((255-b)*pct)) )

# from visUtil import VisUtil
# vu = visUtil('file:stackedbarline2.csv','title:Site Compliance', 'height:6', 'width:12')
# vu.reset_colors(gradient=5, add=['#27C1Be'], default=['#E3C700','#E39000'])
# print(vu.color_cache)
# print(vu.next_color())
# print(vu.next_color())
# print(vu.color_cache)
# print(vu.all_colors())
# vu.reset_colors()
