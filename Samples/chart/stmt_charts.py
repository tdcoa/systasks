#! /usr/bin/env python
"Bar charts to show statement type details"
from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

p = ArgumentParser(description=__doc__)
p.add_argument('input', type=Path, help='Input CSV file')
p.add_argument('freq', nargs='?', type=Path, default=Path('stmt-freq.png'), help='Frequency chart file name')
p.add_argument('cpu', nargs='?', type=Path, default=Path('stmt-cpu.png'), help='CPU chart file name')
p.add_argument('io', nargs='?', type=Path, default=Path('stmt-io.png'), help='IO chart file name')
args = p.parse_args()

df = pd.read_csv(str(Path(args.input)))

sns.set(style="whitegrid")
for x, outf in [("Freq", args.freq), ("TotCPU", args.cpu), ("TotIO", args.io)]:
	plt.clf()
	ax = sns.barplot(x=x, y="StatementType", data=df)
	ax.figure.tight_layout()
	fig = ax.get_figure()
	fig.savefig(outf)
