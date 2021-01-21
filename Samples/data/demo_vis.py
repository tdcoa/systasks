import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
sns.set(rc={'figure.figsize':(11, 4)})

# open file into dataframe:
filename = 'alldates.csv'
df = pd.read_csv(filename)

# adjust columns as needed:
df.cal_date = pd.to_datetime(df.cal_date)
df.today = pd.to_datetime(df.today)
df['event'] = df.item
df['days'] = (df.today - df.cal_date).dt.days
df['years'] = df.days/365
df.sort_values('years',ascending=False,inplace=True)

# graph:
sns.set(style="whitegrid")
ax = sns.barplot(x="item", y="years", data=df)

# save:
fig = ax.get_figure()
fig.savefig(filename.replace('.csv','.png'))
