#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Creating the bilateral hippocampal mask

@author:  jenni.saaristo@helsinki.fi
@version: 2021-06-03
@notes:   checked for publication and ran
"""

import os
import numpy as np
from nilearn import datasets
from nilearn.image import load_img, new_img_like
from nilearn.plotting import plot_img


rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
maskdir = os.path.join(rootdir,'masks')

# Get the HOA subcortical
hoa = datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr25-2mm')
hoaimg = load_img(hoa.maps)

# Get inds of bilateral hippocampus
inds = [hoa.labels.index('Left Hippocampus'), hoa.labels.index('Right Hippocampus')]

# Create mask
data = hoaimg.get_fdata().copy()
data[ np.isin(data, inds, invert=True) ] = 0
data[ np.isin(data, inds, invert=False) ] = 1
plotimg = new_img_like(hoaimg, data)

# Check mask
plot_img(plotimg, cut_coords=(28,-30,-8) )

# Save
plotimg.to_filename(os.path.join(maskdir, 'hipp_thr25_2mm.nii'))

