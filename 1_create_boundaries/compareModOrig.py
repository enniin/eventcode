#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Behavioral data, analyze and plot

@author: jenni.saaristo@helsinki.fi
@version: 2021-08
"""

from os.path import join
import pandas as pd
import numpy as np
import scipy.io.wavfile
import eventseg as es
import matplotlib.pyplot as plt

datadir = '/Users/jenska/code/python/eventsegment/segment_data/behavioral_ratings_data/flat'
origfile = 'behav_flat_orig.csv'
modfile = 'behav_flat_mod.csv'
#audiodir = '/Users/jenska/Desktop/Event segmentation/0 - THEORY ETC/concatenated_story'

#%% Get data
df_orig = pd.read_csv(join(datadir,origfile))
df_mod = pd.read_csv(join(datadir,modfile))
df_parts = pd.read_csv(join(datadir,'partlens.csv'),index_col=0)

#%% Make concat rt
for df in [df_orig, df_mod]:
    df.rename(columns={'Unnamed: 0':'id'}, inplace=True)
    df['rt_concat'] = 0
    for i in df_parts.index:
        p = df_parts.part[i]
        ind = df.query('part == @p').index
        df.loc[ind, 'rt_concat'] = df.loc[ind, 'rt'] + df_parts.start[i]

#%% We'll manually correct the extra boundaries before calculating stats
# The corected go into a dict
corr_dfs = {}
print(df_mod['subj'].unique())
#%% Each subject individually, iterating as needed
s = 6
this_mod = df_mod.query('subj == @s').reset_index(drop=True)
this_orig = df_orig.query('subj == @s').reset_index(drop=True)

# How many more origs (neg means more mods -- not likely)
print(this_orig.count()[0] - this_mod.count()[0])

#%% Spot the extra bounds
diffs = this_orig['rt_concat'][:len(this_mod)].to_numpy() - this_mod['rt_concat'].to_numpy()
#diffs = this_orig['rt_concat'].to_numpy() - this_mod['rt_concat'][:len(this_orig)].to_numpy()

plt.plot(diffs)
plt.title(f'Subject {s}')
plt.show()

#%% Figure out which to drop
i = 12
j = 17
print(this_orig.loc[i:j])
print(this_mod.loc[i:j])

#%% Drop
this_orig = this_orig.drop(index=3).reset_index(drop=True)
#this_mod = this_mod.drop(index=[139]).reset_index(drop=True)

#%% Save
assert len(this_orig) == len(this_mod)
corr_dfs[s] = [this_orig, this_mod]

#%% Calc avg adjustment per subj, and avg of avg
# This gives all subjs an equal weight, and those that made lots of
# annotations don't overwhelm the average.
avgs = []
for s, [this_orig, this_mod] in corr_dfs.items():
    diffs = this_orig['rt_concat'].to_numpy() - this_mod['rt_concat'].to_numpy()
    avgs.append(np.mean(diffs))
print(avgs)
print(np.mean(avgs))
print(np.std(avgs))

# So, calculating from our data the average reaction time is 4.77 secs,
# but the sd is pretty huge as well. So is this really a reasonable estimate
# to use? Does it tell us more about the stimulus or the annotators?
#%% Raw average over all diffs
all_diffs = []
for s, [this_orig, this_mod] in corr_dfs.items():
    diffs = this_orig['rt_concat'].to_numpy() - this_mod['rt_concat'].to_numpy()
    all_diffs.extend(diffs)
print(np.mean(all_diffs))
print(np.std(all_diffs))

# With this method the average reaction time becomes 2.93 sec. Which makes more
# sense? Those who make more annotations have smaller, diffs -- do they also
# have more effect on the final boundaries? Maybe they do? Then perhaps 3 secs
# is a more reasonable estimate.

#%% Save as pickle so we don't have to do this ever again...
np.save(join(datadir,'orig_mod_trimmed.npy'), corr_dfs, allow_pickle=True)

