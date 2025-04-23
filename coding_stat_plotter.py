#!/usr/bin/env python
# author: Bergk Pinto Benoît
# aim: plot stats from a stats generated file for time spent on coding

from pathlib import Path
import pandas
import matplotlib.pyplot as plt

import datetime

STATFILE = '/home/bioinfocyto/.emacs.d/coding_history'


data = pandas.read_csv(STATFILE, sep='\t', names=[
                       'date', 'duration', 'language', 'file', 'directory'])
data['date'] = [x.split(' ')[0] for x in data['date']]
# data['date'] = pandas.to_datetime(data['date'], format = '%Y-%m-%d')
data['duration'] = [datetime.timedelta(hours=int(x.split(':')[0]), minutes=int(x.split(
    ':')[1]), seconds=int(x.split(':')[2].split('.')[0])).total_seconds()/(60*60)for x in data['duration']]

# make a pie chart of the language used in general
sums = data[['duration', 'language']].groupby(
    'language').sum(numeric_only=True)
fig, ax = plt.subplots()
ax.pie(sums['duration'], labels=sums.index)
plt.savefig("coding_pie_charts.pdf", format="pdf", bbox_inches="tight")
plt.close()

# make a pie chart of the main directories used in the coding time
sums = data[['duration', 'directory']].groupby(
    'directory').sum(numeric_only=True)
fig, ax = plt.subplots()
ax.pie(sums['duration'], labels=sums.index)
plt.savefig("projects_pie_charts.pdf", format="pdf", bbox_inches="tight")
plt.close()


# for each language in the file produce a barchart
for lang in data['language'].unique():
    language_data = data[data['language'] == lang]
    sum_by_day = language_data.groupby('date').sum()
    # print(sum_by_day)
    fig, ax = plt.subplots()
    plt.bar(sum_by_day.index, sum_by_day['duration'])
    plt.ylabel('Hours of coding')
    plt.xlabel('Days')
    plt.savefig(f"{lang}_bar_chart.pdf", format="pdf", bbox_inches="tight")
    plt.close()
