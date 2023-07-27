#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Get the betas for the main bounds vs perms analysis

@author:  jenni.saaristo@helsinki.fi
@version: 2021-12-02
@notes:   Average ROIs across participants
"""
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Global locations
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
savedir = os.path.join(rootdir, 'fmri-data','ini-roi')
roifile = 'tc_hoahc_concat.csv'
df_subj = pd.read_csv(os.path.join(rootdir,'scripts','subj_info.csv'))

#%% Average ROI tcs across participants

tic = time.time()

# Take first subject as base for summing
subj = df_subj.subj[0]
print(subj)
roipath = os.path.join(savedir,subj,roifile)
df_roi_sum = pd.read_csv(roipath, index_col=0)

# Loop thru the rest
subjs = df_subj.subj[1:]
for subj in subjs:
    print(subj)
    roipath = os.path.join(savedir,subj,roifile)
    df_roi = pd.read_csv(roipath, index_col=0)
    df_roi_sum = df_roi_sum + df_roi

df_roi_avg = df_roi_sum / len(df_subj)
toc = time.time()
print(toc-tic)

#%% Sanity checks

areas = df_roi.columns
plt.plot(df_roi_avg[areas[48]]) # HC
plt.plot(df_roi_avg[areas[29]]) # PCC
plt.plot(df_roi_avg[areas[30]]) # precuneus
plt.plot(df_roi_avg[areas[49]]/10) # run ind
#plt.plot(df_roi_avg[areas[0]])  # frontal pole, should not correlate at all

#%%
print(np.corrcoef(df_roi_avg[areas[29]], df_roi_avg[areas[30]]))

#%% Save
df_roi_avg.to_csv(os.path.join(savedir,'tc_hoahc_concat_avg.csv'))
