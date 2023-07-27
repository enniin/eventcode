#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
fix the audio gaps into fMRI time

@author: jenska
"""

import os
import pandas as pd

datadir = '/Users/jenska/code/python/eventsegment/segment_data/behavioral_ratings_data/out'
gapfile = 'all_audiogaps.csv'
partfile = 'partlensf.csv'

#%% Get data
df_gaps = pd.read_csv(os.path.join(datadir,gapfile))
df_parts = pd.read_csv(os.path.join(datadir,partfile),index_col=0)

#%% Fix to fMRI time (which is audio time -1 sec)
df_fgaps = df_gaps.copy()
df_fgaps['off_frt'] = df_fgaps['audio_off'] - 1
inds = df_fgaps.query('off_frt <= 0').index
df_fgaps = df_fgaps.drop(index=inds).reset_index(drop=True)

print(len(inds))

# calc audio on
df_fgaps['on_frt'] = df_fgaps['off_frt'] + df_fgaps['gap_dur']
print(df_fgaps)

#%% Calc concat times
for i in df_parts.index:
    inds = df_fgaps.query('part == @df_parts.part[@i]').index
    df_fgaps.loc[inds,'off_frt_concat'] = df_fgaps.off_frt[inds] + df_parts.fstart[i]
    df_fgaps.loc[inds,'on_frt_concat'] = df_fgaps.on_frt[inds] + df_parts.fstart[i]
print(df_fgaps)

#%% Save
df_fgaps.to_csv(os.path.join(datadir,'all_audiogaps_f.csv'))