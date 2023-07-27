#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Ploooot ROI results on glassbrain & surface

@author:  jenni.saaristo@helsinki.fi
@version: 2021-0
@notes:   
"""

from os.path import join
import pandas as pd
import numpy as np
from nilearn import datasets
from nilearn import plotting
from nilearn import image
from nilearn import surface

# Global locations
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
maskdir = join(rootdir,'masks')
resdir = join(rootdir,'scripts/5_analyses_plots/out')

#%% Get mask
hoa = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm', maskdir)
nii_mask = image.load_img(hoa.maps)
fdata = nii_mask.get_fdata().copy()
plotting.plot_roi(nii_mask)

#%% Get results
resfile = 'audioperm_results_3s.csv'
df_results = pd.read_csv(join(resdir,resfile))
inds = df_results.query('area == "Hippocampus"').index
df_results.drop(index=inds, inplace=True)

#%% Threshold data

# create a mask of p_adj > 0.05
p_mask = fdata.copy()
p_mask[p_mask == 0] = np.nan
for i in df_results.index:
    area = df_results.area[i]
    p = df_results.p_adj[i]
    m_i = hoa.labels.index(area)
    p_mask[p_mask == m_i] = p
p_mask = np.where(p_mask < 0.05, 1, 0)

# create a mask of betas
b_mask = fdata.copy()
b_mask[b_mask == 0] = np.nan
for i in df_results.index:
    area = df_results.area[i]
    b = df_results.beta[i]
    m_i = hoa.labels.index(area)
    b_mask[b_mask == m_i] = b

# create the final thresholded data
pb_mask = np.where(p_mask == 1, b_mask, 0)

#%% create nii and plot glass brain
nii_plot = image.new_img_like(nii_mask, pb_mask)
plotting.plot_glass_brain(nii_plot, black_bg=False, display_mode='xz', colorbar=True)

#%% plot surf
fsaverage = datasets.fetch_surf_fsaverage('fsaverage')
result_3D = surface.vol_to_surf(nii_plot, fsaverage.pial_left)

plotting.plot_surf_stat_map(fsaverage.infl_left, result_3D, colorbar=True, black_bg=True,
                            threshold=1, view='medial', bg_map=fsaverage.sulc_left)
plotting.plot_surf_stat_map(fsaverage.infl_left, result_3D, colorbar=True,
                            threshold=1, view='lateral', bg_map=fsaverage.sulc_left)

#%% plot stat map mmm nope
plotting.plot_stat_map(nii_plot, cut_coords=[2,-40,30])
