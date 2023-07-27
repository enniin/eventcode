#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Make design matrices for bounds and perms

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-26
@note:    Audioboundaries (bound gaps vs non-bound gaps)
"""

from os.path import join
import pandas as pd
import numpy as np

from nilearn import plotting
from nilearn.glm import first_level

#datadir = '/m/nbe/scratch/alex/private/jenni/eventseg/scripts'
dataroot = '/Users/jenska/code/python/eventcode'
indir = join(dataroot,'1_create_boundaries/out')
outdir = join(dataroot,'2_make_design_matrices/out')

react_time = '3s'
boundfile = f'audiobounds_f{react_time}.csv'
permfile = f'audioperms_f{react_time}.npy'
boundout = f'dm_audiobounds_{react_time}.csv'
permout = f'dm_audioperms_{react_time}.csv'

#%% Get boundaries and make DM

df_bounds = pd.read_csv(join(indir,boundfile),index_col=0)
df_bounds['frt'] = df_bounds['on_frt'] - df_bounds['gap_dur']/2  # add frt
df_parts = pd.read_csv(join(indir,'partlensf.csv'),index_col=0)

# Make boundary dm run-by-run
dm = pd.DataFrame()
for i in df_parts.index:
    times = np.arange(df_parts.flen[i]) # fmri times
    
    inds = df_bounds.query('part == @df_parts.part[@i]').index
    events = pd.DataFrame()
    events['onset'] = df_bounds.frt[inds] # fmri time
    events['duration'] = 0
    events['trial_type'] = 'bound'
    
    this_dm = first_level.make_first_level_design_matrix(times, events,
                          drift_model='polynomial', drift_order=3)
    this_dm['constant'] = i
    dm = dm.append(this_dm, ignore_index=True)

# plot design (or part of it)
plotting.plot_design_matrix(dm)

#%% Save the DM
dm.to_csv(join(outdir,boundout))

#%%
'''
It is in fact enough to have the main dm part-wise: we get the drifts correctly,
and the constants for runind. The perms then line up with those.
'''
#%% Make DM of perms
# These are already frt_concat
perms = np.load(join(indir, permfile))

# To get a regressor for each perm we need to code them as trial types
df_perms = pd.DataFrame()
p = pd.DataFrame()

for i in range(perms.shape[1]):
    p['onset'] = perms[:,i]
    p['duration'] = 0
    p['trial_type'] = i
    df_perms = df_perms.append(p, ignore_index=True)

df_perms.sort_values(by='onset', inplace=True, ignore_index=True)

#%%
# Create DM, hello slow
times = np.arange(df_parts.flen.sum())
dm_perm = first_level.make_first_level_design_matrix(times, df_perms,
                          drift_model=None)

#%% Plot a random dm
p = 30
#print(df_perms.query('trial_type == @p'))
#plotting.plot_design_matrix(dm_perm.loc[:,p:p+1])
plotting.plot_design_matrix(dm_perm.loc[:,50:80])

#%% Save perm dm
dm_perm.to_csv(join(outdir,permout)) # around 55 MB

# Left in the constant, much too scared of crashing everything...