#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Make DM for beta series (salience modulation analysis)

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@note:    Fixing the fMRI timing issue & adding new react time

"""

import os
import pandas as pd
import numpy as np

from nilearn import plotting
from nilearn.glm import first_level

#datadir = '/m/nbe/scratch/alex/private/jenni/eventseg/segmentdata'
dataroot = '/Users/jenska/code/python/eventcode'
indir = os.path.join(dataroot,'1_create_boundaries/out')
outdir = os.path.join(dataroot,'2_make_design_matrices/out')

react_time = '3s'
boundfile = f'boundaries_f{react_time}.csv'
dmout = f'dm_series_{react_time}.csv'

#%% Get boundaries and parts
df_bounds = pd.read_csv(os.path.join(indir,boundfile),index_col=0)
df_parts = pd.read_csv(os.path.join(indir,'partlensf.csv'),index_col=0)

#%% Create DM

# Let's not ignore the post-hocs, but allow them to be modeled
#df_boundsreal = df_bounds[df_bounds.id != 999]

# Make DM partwise to get drifts correctly
dm = pd.DataFrame()
for i in df_parts.index:
    times = np.arange(df_parts.flen[i])
    
    # define events
    inds = df_bounds.query('part == @df_parts.part[@i]').index
    events = pd.DataFrame()
    events['onset'] = df_bounds.frt[inds]  # use fMRI time
    events['duration'] = 0
    events['trial_type'] = df_bounds.id[inds].astype(int)
    
    # make DM
    this_dm = first_level.make_first_level_design_matrix(times, events,
                          drift_model='polynomial', drift_order=3)
    this_dm['constant'] = i
    
    # concatenate to previous
    dm = dm.append(this_dm, ignore_index=True)

# Fix nans
# nans happen when a part has no events at all – i.e. all the time in this model
for cn in dm.columns:
    inds = dm[cn].isna()
    dm.loc[inds, cn] = 0

# Reorganise columns (boundaries first, confounds last)
dc_inds = dm.columns.str.contains('drift|constant', regex=True, na=False)
cols = dm.columns[np.invert(dc_inds)].append(dm.columns[dc_inds])
dm = dm[cols]

# Plot DM
plotting.plot_design_matrix(dm)

#%% Save
dm.to_csv(os.path.join(outdir,dmout))


