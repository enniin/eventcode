#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Make FIR regressors

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-16
@note:    Fixing the fMRI timing issue, experimenting
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from nilearn import plotting
from nilearn.glm import first_level

#datadir = '/m/nbe/scratch/alex/private/jenni/eventseg/segmentdata'
dataroot = '/Users/jenska/code/python/eventcode'
indir = os.path.join(dataroot,'1_create_boundaries/out')
outdir = os.path.join(dataroot,'2_make_design_matrices/out')
boundfile = 'boundaries_f3s.csv'

#%% Get data
df_bounds = pd.read_csv(os.path.join(indir,boundfile),index_col=0)
df_parts = pd.read_csv(os.path.join(indir,'partlensf.csv'),index_col=0)

# Drop post hoc bounds for now
inds = df_bounds.query('id == 999').index
df_bounds = df_bounds.drop(index=inds).reset_index(drop=True)

#%% Check saliency structure
plt.hist(df_bounds['nobs'], 18)
plt.show()

#%% Shift boundaries so we're able to plot negative values
# has to be done with frt, as dms are created part-wise
df_bounds.frt = df_bounds.frt - 5
df_bounds.frt_concat = df_bounds.frt_concat - 5

# We have to drop the ones that go outside part
inds = df_bounds.query('frt < 0').index
print(df_bounds.loc[inds,:]) # low=1, mid=2, high=1 / mid=1
df_bounds.drop(index=inds, inplace=True)

#%% Check segment lengths (print all less than 10 secs)
df = df_bounds
prev_j = None
for j in df.index:
    if prev_j == None:
        prev_j = j
        continue
    else:
        this_frt = df.frt_concat[j]
        prev_frt = df.frt_concat[prev_j]
        if (this_frt - prev_frt < 10):
            print(df.loc[prev_j])
            print(df.loc[j])
        prev_j = j

#%% Drop bounds 1 and 10 (then all seglens > 9 sec)
df_bounds = df_bounds.drop(index=[1,10])

#%% Define bins
br1 = 7
br2 = 10
print(df_bounds.query('nobs > 1')['nobs'].describe())
print(df_bounds.query('nobs > 1 & nobs < @br1')['nobs'].count())
print(df_bounds.query('nobs >= @br1 & nobs < @br2')['nobs'].count())
print(df_bounds.query('nobs >= @br2 ')['nobs'].count())
plt.hist(df_bounds['nobs'], bins=[2, br1, br2, 18])
plt.show()

#%% Separate by bins
binned = dict()
binned['low'] = df_bounds.query('nobs > 1 & nobs < @br1')
binned['mid'] = df_bounds.query('nobs >= @br1 & nobs < @br2')
binned['high'] = df_bounds.query('nobs >= @br2')
# Make one dm for the grand average
binned['all'] = df_bounds

#%% Make DMs (part-wise)
dms = dict()
for key,df in binned.items():
    dm = pd.DataFrame()
    for i in df_parts.index:
        times = np.arange(df_parts.flen[i])
        
        inds = df.query('part == @df_parts.part[@i]').index
        events = pd.DataFrame()
        events['onset'] = df.frt[inds]   # use fMRI adjusted time
        events['duration'] = 0
        events['trial_type'] = 'x'
        
        this_dm = first_level.make_first_level_design_matrix(times, events,
                              hrf_model='fir', fir_delays=np.arange(0,16),
                              drift_model='polynomial', drift_order=3)
        this_dm['constant'] = i
        dm = dm.append(this_dm, ignore_index=True)
    dms[key] = dm

#plotting.plot_design_matrix(this_dm)
#%% Fix nans (they happen when there's no event in the part at all)
for (key, dm) in dms.items():
    for cn in dm.columns:
        inds = dm[cn].isna()
        dm.loc[inds, cn] = 0

#%% Plot design (or part of it)
plotting.plot_design_matrix(dms['low'])
plotting.plot_design_matrix(dms['mid'])
plotting.plot_design_matrix(dms['high'])
plotting.plot_design_matrix(dms['all'])

#%% plot example FIR delays for one run
for i in range(12):
    plt.plot(this_dm['x_delay_'+str(i)])
plt.show()

#%% Save the design matrices
for (key, dm) in dms.items():
    dm.to_csv(os.path.join(outdir,f'dm_fir3s_{key}.csv'))

