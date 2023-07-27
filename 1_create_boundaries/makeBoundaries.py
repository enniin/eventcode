#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Make final boundaries set

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-16
@notes:   Fixing the fMRI timing issue, new calculated reaction time
"""

import os
import pandas as pd
import numpy as np
from evseg import combine, boundplot
import matplotlib.pyplot as plt

datadir = '/Users/jenska/code/python/eventsegment/segment_data/behavioral_ratings_data/flat'
outdir = '/Users/jenska/code/python/eventcode/1_create_boundaries/out'
datafile = 'segment_data_full.csv'

#%% Get data
df = pd.read_csv(os.path.join(datadir,datafile),index_col=0)
df_parts = pd.read_csv(os.path.join(outdir,'partlensf.csv'),index_col=0) 

#%% -----------------  PRE-CHAINING ADJUSTMENTS  -------------------------
#%% Remove reaction time

# The idea here is to account for an inherent lag in making boundary
# judgements. In the thesis I will use two different strategies for the
# reaction time: 1) I'll basically copy the one used in Ben-Yakov & Henson
# (2018) and round it up to 1 sec, and 2) estimate a reaction time specific
# to this stimulus from the corrected annotations by the first annotators.
# (See compareModOrig.py for the method.) The estimated reaction time is 3 sec.

# Change when needed
react_time = 3

df_concat = df.copy()
df_concat['rt'] = df_concat['rt'] - react_time 
# fix negative rt's, because they don't really make sense
inds = df_concat.query('rt < 0').index
df_concat.loc[inds, 'rt'] = 0

#%% Add concatenated rts
df_concat['rt_concat'] = 0
for i in df_parts.index:
    p = df_parts.part[i]
    ind = df.query('part == @p').index
    df_concat.loc[ind, 'rt_concat'] = df_concat.loc[ind, 'rt'] + df_parts.start[i]

#%% Save this dataset (if we need to checkParams again)
df_concat.to_csv(os.path.join(datadir,'segment_data_concat.csv'))

#%% -------------------------- CHAINING ----------------------------------
#%% Combine boundaries

# define bridge lengths & combine (based on checkParams)
br1 = 1.5
br2 = 4
(df_bounds, df_full) = combine.chain_concat(df_concat,df_parts,br1,br2)

#%% Plot on time with thresholding

th = 4 # this should also come from checkParams

fig, axs = plt.subplots(nrows=5,ncols=2,figsize=(14,10),constrained_layout=True)
axs = boundplot.trim_axs(axs,10)

for i in df_parts.index:
    p = df_parts.iloc[i,0]
    cdfs = df_bounds.query('part == @p & nobs > @th')
    boundplot.plot_no_sound(cdfs,df_parts.query('part == @p').iloc[0,1],
                        title='Chapter ' + str(p),
                        legend=False, ax=axs[i])

#%% Threshold the boundary data
th = 4
inds = df_bounds.query('nobs > @th').index
df_boundth = df_bounds.iloc[inds]

#%% Calculate some stats & plot
print(df_boundth['clen'].describe())
segs = np.empty(0)
for i in df_parts.index:
    this_seg = combine.to_segments(df_boundth[df_boundth.part == df_parts.part[i]]['rt'],
                                 len_total = df_parts.len[i])
    segs = np.append(segs,this_seg)

print(np.mean(segs))
print(min(segs))
print(max(segs))
plt.hist(segs, bins=50)

del(i,ind,inds,fig,this_seg,p)
#%%

#%% -----------------  POST-CHAINING ADJUSTMENTS  -------------------------
#%% Add chapter boundaries

# Whenever we have a chapter start, and no boundary anywhere in sight, we'll
# add a "ghost boundary" with id=999. Do the same for chapter endings.

df_chapters = df_boundth.copy()

# Gather the audio onsets & offsets and calc their rt_concat location, then
# check if there's a boundary inside a reasonable distance from it -- if not,
# add a new boundary (reasonable here meaning that the results make sense, and
# we don't get a 4 sec segment where there really isn't cause to have one)

onset_concat = df_parts['start'] + df_parts['onset']
offset_concat = df_parts['start'] + df_parts['offset']
win = 5  # this is the main window
win2 = 2 # this is just to give some leeway for timing

# We'll give these boundaries the max nObs because they are by definition salient
nobs = df_chapters.nobs.max()  

# check onsets
for i in onset_concat.index:
    onset = onset_concat[i]
    dfi = df_boundth.query('rt_concat > @onset-@win2 & rt_concat < @onset+@win')
    if dfi.empty:
        part = df_parts.part[i]
        rt = df_parts.onset[i]
        newbound = {'id':999,'part':part,'rt':rt,'rt_concat':onset,'clen':0,'nobs':nobs}
        df_chapters = df_chapters.append(newbound, ignore_index=True)
        print(newbound)

# check offsets
for i in offset_concat.index:
    offset = offset_concat[i]
    dfi = df_boundth.query('rt_concat > @offset-@win & rt_concat < @offset+@win2')
    if dfi.empty:
        part = df_parts.part[i]
        rt = df_parts.offset[i]
        newbound = {'id':999,'part':part,'rt':rt,'rt_concat':offset,'clen':0,'nobs':nobs}
        df_chapters = df_chapters.append(newbound, ignore_index=True)
        print(newbound)

# reorder the dataset and fix indices
df_chapters = df_chapters.sort_values(by=['rt_concat']).reset_index(drop=True)
print(df_chapters)

#%% Plot on time to check final boundaries
fig, axs = plt.subplots(nrows=5,ncols=2,figsize=(14,10),constrained_layout=True)
axs = boundplot.trim_axs(axs,10)

for i in df_parts.index:
    p = df_parts.iloc[i,0]
    dfi = df_chapters.query('part == @p')
    boundplot.plot_no_sound(dfi,df_parts.query('part == @p').iloc[0,1],
                        title='Chapter ' + str(p),
                        legend=False, ax=axs[i])

#%% Save MEG boundaries (without the fMRI correction)
df_chapters.to_csv(os.path.join(outdir,f'boundaries_meg_{react_time}s.csv'))

#%% Adjust to fMRI time
""" The issue here is that the fMRI data actually starts not at 0 sec but
1 sec on the audio timeline. This is due to the temporal smoothing algorithm,
which ditches the first and last second of the data. So to compensate, we have
to shift the boundaries -1 sec so they reflect the timing of the fMRI data.
We'll also ditch all boundaries that happened to reside in that time window.
"""

# fMRI time is audio time - 1
df_fbounds = df_chapters.copy()
df_fbounds['frt'] = df_fbounds['rt'] - 1
inds = df_fbounds.query('frt <= 0').index
df_fbounds = df_fbounds.drop(index=inds).reset_index(drop=True)
print(len(df_fbounds))
# we're left with 79 bounds

# Also create the frt_concat while we're at it
df_fbounds['frt_concat'] = 0
for p in df_parts.part:
    inds = df_fbounds.query('part == @p').index
    df_fbounds.loc[inds,'frt_concat'] = df_fbounds['frt'] + df_parts.fstart[p-1]
print(df_fbounds)

#%% Save bounds
df_fbounds.to_csv(os.path.join(outdir,f'boundaries_f{react_time}s.csv'))

