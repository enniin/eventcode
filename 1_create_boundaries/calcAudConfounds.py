#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Calculate confounds for boundaries based on audio features

@author:  jenni.saaristo@helsinki.fi
@version: 2021-09-25
@notes:   First draft
"""

from os.path import join
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

audiodir = '/m/nbe/scratch/alex/stimuli/wav/concatenated_story'
datadir = '/m/nbe/scratch/alex/private/jenni/eventseg/scripts/1_create_boundaries/out'

boundfile = 'boundaries_f1s.csv'

#%% Get dfs
df_bounds = pd.read_csv(join(datadir,boundfile), index_col=0)
df_gaps = pd.read_csv(join(datadir,'all_audiogaps_f.csv'), index_col=0)
df_parts = pd.read_csv(join(datadir,'partlensf.csv'), index_col=0)
parts = df_parts.part.unique()

#%% Read envelopes
d = 10 # srate in Hz
envs = {}
for p in parts:
    envs[p] = np.load(join(audiodir, f'kappale{p}_envelope_{d}Hz.npy'))

#%% Plot to check
fig, axs = plt.subplots(5,2,sharey=True)
axs = axs.flatten()
for p in parts:
    gs = df_gaps.query('part == @p').audio_off.to_numpy()*d
    axs[p-1].plot(envs[p], linewidth=0.4)
    axs[p-1].scatter(gs, np.zeros_like(gs), c='r')

#%% To have some meaningful measure of volume let's make these percentages
max_all = max([max(e) for e in envs.values()])
for p in parts:
    envs[p] /= max_all

#%% Calc meanvol

win = 1 * d # window (sec) * Hz of env
half = int(win/2)

for p in parts:
    inds = df_bounds.query('part == @p').index
    rts = df_bounds.loc[inds, 'rt'].to_numpy() * d
    rts = rts.astype(int)
    
    # Gather epochs with len=win around rts (symmetric)
    epochs = np.zeros((len(rts),win))
    for i in range(len(rts)):
        epochs[i,:] = envs[p][ rts[i]-half : rts[i]+half ]
    
    # Calculate mean vol and vol difference (where > 0 means increasing vol)
    meanvol = epochs.mean(axis=-1)
    voldiff = epochs[:,half+1:].mean(axis=-1) - epochs[:,:half+1].mean(axis=-1)
    
    # Copy to df
    df_bounds.loc[inds,'meanvol'] = meanvol
    df_bounds.loc[inds,'voldiff'] = voldiff

#%% Save
df_bounds.to_csv(join(datadir, 'boundaries_f1s_vol.csv'))

#%% Some checks
p = 3
rts = df_bounds.query('part == @p').rt.to_numpy()*d
plt.plot(envs[p], linewidth=0.4)
plt.scatter(rts, np.zeros_like(rts), c='r')

print(df_bounds.query('part == @p'))

#%%