import importlib.util
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

lib_path = Path(__file__).parent / "coaVizLib.py"
spec = importlib.util.spec_from_file_location("coaVizLib", lib_path)
coaVizLib = importlib.util.module_from_spec(spec)
sys.modules["coaVizLib"] = coaVizLib
spec.loader.exec_module(coaVizLib)

def coaprint(*args):
   # print(*args)
   return None
def args2dict(args):
   kwargs = {}
   for arg in args:
       goodsyntax = False
       if ':' in arg:
           argobj = arg.split(':')
           if len(argobj) > 1:
               kwargs[argobj[0]] = arg[len(argobj[0]) + 1:]
               goodsyntax = True
       if not goodsyntax:
           coaprint('Supplied arg not conformed to name:value syntax requirements:\t%s' % str(arg))
   if 'yintercept' not in kwargs and 'ymin' in kwargs: kwargs['yintercept'] = kwargs['ymin']
   if 'csvfile' not in kwargs and 'file' in kwargs: kwargs['csvfile'] = kwargs['file']
   return dict(kwargs)
def combine_bar_line_chart(**kwargs):
   coaprint('combine_bar_line_chart Started')
   coaprint('args:', kwargs)
   # Define all variables, with defaults
   errorcondition = False
   if 'csvfile' not in kwargs: errorcondition = True
   else: csvfile = kwargs['csvfile']
   if 'x_column' not in kwargs: errorcondition = True
   else: x_column = kwargs['x_column']
   if 'title' in kwargs: title = kwargs['title']
   else: title = ''
   if 'height' in kwargs: height = float(kwargs['height'])
   else: height = 6
   if 'width' in kwargs: width = float(kwargs['width'])
   else: width = 12
   if 'save' in kwargs: save = kwargs['save'].lower() == 'true'
   else: save = True
   show_percentage = kwargs.get('show_percentage', 'false').lower() == 'true'
   bar_columns = kwargs.get('bar_columns', '').split(',')
   bar_colors = kwargs.get('bar_colors', '').split(',')
   line_columns = kwargs.get('line_columns', '').split(',')
   line_colors = kwargs.get('line_colors', '').split(',')
   if errorcondition:
       msg = 'Error occurred while validating parameters, please check your parameters, documentation, and try again. \nParameters: %s' % str(kwargs)
       coaprint(msg)
       return msg
   # Read and process data
   df = pd.read_csv(csvfile)
   x = df[x_column]
   if title == '': title = csvfile.split('.')[0].split('--')[-1].replace('_', ' ').upper()
   coaprint('x axis column: ', title)
   # Build the graph figure, assign settings
   fig, ax1 = plt.subplots(figsize=(width, height))
   indices = np.arange(len(x))
   bar_width = 0.35  # Adjust bar width to be narrower
   gap_between_clusters = 0.04  # Gap between clusters of bars for different months
   total_bar_width = len(bar_columns) * (bar_width + gap_between_clusters)  # Total width of each bar cluster
   if bar_columns[0]:
       # Bar chart
       for i, col in enumerate(bar_columns):
           color = bar_colors[i] if i < len(bar_colors) else None
           bar_positions = indices + i * bar_width + i * gap_between_clusters  # Adjusted bar positions
           bars = ax1.bar(bar_positions, df[col], bar_width, label=col, color=color)
           # Add data labels to the bars
           for bar in bars:
               height = bar.get_height()
               label = f'{height:.1f}%' if show_percentage else f'{height:.1f}'
               ax1.annotate(label,
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=9)
       ax1.set_xlabel(kwargs['x_column'])
       # ax1.set_ylabel('Counts (Millions)')
       ax1.set_xticks(indices + (total_bar_width - gap_between_clusters) / 2)
       ax1.set_xticklabels(x, rotation=0, ha='right')  # Adjusted alignment to center
       ax1.yaxis.grid(True, linestyle='--', linewidth=0.5)  # Add light horizontal gridlines
   if line_columns[0]:
       # Line chart
       for i, col in enumerate(line_columns):
           color = line_colors[i] if i < len(line_colors) else None
           line_positions = indices + (total_bar_width - gap_between_clusters) / 2  # Align with bar clusters
           ax1.plot(line_positions, df[col], label=col, color=color, marker='o', linewidth=2)
       ax1.set_xlabel(kwargs['x_column'])
       # ax1.set_ylabel('Counts (Millions)')
       # ax1.set_xticks(indices + (total_bar_width - gap_between_clusters) / 2)
       ax1.set_xticklabels(x, rotation=0, ha='center')  # Adjusted alignment to center
       ax1.yaxis.grid(True, linestyle='--', linewidth=0.5)  # Add light horizontal gridlines
   # Combine legends
   lines, labels = ax1.get_legend_handles_labels()
   ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
   plt.title(title, pad=40)
   fig.tight_layout()
   # Remove the box (spines)
   for spine in ax1.spines.values():
       spine.set_visible(False)
   if save:
       plt.savefig(csvfile.replace('.csv', '.png'), bbox_inches='tight')
   else:
       plt.show()
# Execute the function with command line arguments
combine_bar_line_chart(**args2dict(sys.argv[1:]))