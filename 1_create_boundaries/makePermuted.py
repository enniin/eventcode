#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Permuting sham sets

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@notes:   Fixing the fMRI timing issue & adding new react time
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from evseg import combine

dataroot = '/Users/jenska/code/python/eventcode/'
outdir = os.path.join(dataroot,'1_create_boundaries/out')
react_time = '3s'
#datafile = f'boundaries_f{react_time}.csv'
datafile = f'boundaries_meg_{react_time}.csv'

#%% Get boundaries & parts
df_bounds = pd.read_csv(os.path.join(outdir,datafile),index_col=0)
df_parts = pd.read_csv(os.path.join(outdir,'partlensf.csv'),index_col=0)

#%% Plot the nObs histogram
bins = np.arange(19)-0.5
fig1 = plt.hist(df_bounds.nobs, bins=bins, rwidth=0.8)
plt.xticks(np.arange(5,18,1))
plt.xlim(4,18)
plt.xlabel('nObs')
plt.ylabel('boundaries')
plt.show()

#%% Get the segments for permutation
# We want to avoid getting sham boundaries on the "silent" fMRI tail signal,
# so we'll use the audio timeframe and correct to fMRI later
segs = combine.to_segments(df_bounds['rt_concat'], df_parts.len.sum())
plt.hist(segs, bins=50)
plt.xlabel('segment length (sec)')
plt.ylabel('count')
plt.show()

#%% Create permuted boundaries from segments
perms = combine.make_permutations(segs, n=1000)

#%% Plot all to check randomness
lines = np.vstack([np.ones(len(perms))*i for i in range(1000)]).T
plt.scatter(perms, lines, s=1, c='k')
plt.show()
del(lines)
#%% Save perms for MEG (without fMRI correction)
np.save(os.path.join(outdir, f'perms_meg_{react_time}.npy'), perms, allow_pickle=False)

#%% 
""" The perms are now in the audio timeframe, but we want to have them in fMRI
time to be readily used in the design matrices. We also remove the 1 sec fMRI
offset, though it's not strictly necessary.
"""
N = perms.shape[1]
perms_frtcat = np.zeros_like(perms)
for i in range(N):
    
    these_perms = perms[:,i]
    perms_frtcat[:,i] = these_perms
    
    # Calculate the base frt_concat
    for j in range(1,len(df_parts)):
        mask = these_perms > df_parts.start[j]
        perms_frtcat[mask,i] = these_perms[mask] - df_parts.start[j] + df_parts.fstart[j]
    
    # Remove the 1 sec fMRI offset
    perms_frtcat[:,i] = perms_frtcat[:,i] - 1
        
del(i,j)
#%% Plot all to check shift
lines = np.vstack([np.ones(len(perms_frtcat))*i for i in range(1000)]).T
plt.scatter(perms_frtcat, lines, s=1, c='r')
lines = np.vstack([np.ones(len(perms))*i for i in range(1000)]).T
plt.scatter(perms, lines, s=1, c='k')
plt.show()
del(lines)

#%% Save the whole set
np.save(os.path.join(outdir, f'perms_f{react_time}.npy'), perms_frtcat, allow_pickle=False)

