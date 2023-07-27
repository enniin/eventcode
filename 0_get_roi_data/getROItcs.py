#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Getting ROI time courses from ini-data

@author:  jenni.saaristo@helsinki.fi
@version: 2021-07-01
@notes:   checked for publication (audio confound removed, independent running,
                                   using new HC mask)
"""

import os
import sys
import time
from joblib import Parallel, delayed
from nilearn import datasets
from nilearn.input_data import NiftiLabelsMasker
import numpy as np
import pandas as pd

# Global locations
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
savedir = os.path.join(rootdir, 'fmri-data','ini-roi')
maskdir = os.path.join(rootdir,'masks')
inidir = '/m/nbe/scratch/alex/private/maria/alex/ini-data'
nii = '_mni152_maxCorr10_LP4Hz_smoothed6_tsm2.nii'

# =============================================================================
#
# =============================================================================

def getROItcs(subj):

    tic = time.time() # Start

    savepath = os.path.join(savedir,subj)
    if not os.path.isdir(savepath):
        os.makedirs(savepath)

    joblog = open(os.path.join(savepath,'roi_extraction_log.txt'), 'w')
    joblog.write('Started '+ subj + ': '+ time.asctime(time.localtime(tic)) + '\n')
    joblog.write('PID: '+ str(os.getpid()) + '\n')

    try:
        # We need to redirect stdout to log nilearn output
        origout = sys.stdout
        sys.stdout = joblog

        # Get masks
        combhip = os.path.join(maskdir,'hipp_thr25_2mm.nii')
        hcmasker = NiftiLabelsMasker(labels_img=combhip, standardize='zscore',
                               detrend=True, memory='nilearn_cache', verbose=5)
        hoa = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm', maskdir)
        hoamasker = NiftiLabelsMasker(labels_img=hoa.maps, standardize='zscore',
                               detrend=True, memory='nilearn_cache', verbose=5)

        # Get the data
        runs = list(range(2,12)) # story is in runs 2–11
        tcs = np.empty((0,50))

        joblog.write('Extracting ROIs...')
        for i in range(10):

            # make ini filename
            run = runs[i]
            fname = 'acc' + str(run) + nii
            inifile = os.path.join(inidir, subj, 'run'+str(run), fname)

            # get timecourses for hoa ROIs + hc
            hoa_tc = hoamasker.fit_transform(inifile)
            hc_tc = hcmasker.fit_transform(inifile)
            runind = np.ones(hc_tc.shape)*i

            # hstack all ROIs
            tc = np.hstack((hoa_tc,hc_tc,runind))
            # vstack to previous runs
            tcs = np.vstack((tcs,tc))

        sys.stdout = origout

        # Create data frame
        cols = hoa.labels[1:]
        cols.extend(['Hippocampus', 'runind'])
        df_roi = pd.DataFrame(data=tcs, columns=cols)
        df_roi['runind'] = df_roi['runind'].astype(int)

        # Save data
        df_roi.to_csv(os.path.join(savepath,'tc_hoahc_concat.csv'))

        joblog.write(f"Done. TRs extracted: {str(len(tcs))}\n\n")
        toc = time.time() # End
        joblog.write('Ended: '+ time.asctime(time.localtime(toc)) + '\n')
        joblog.close()

    except Exception as e:
        sys.stdout = origout
        toc = time.time() # End
        joblog.write('Error occured:' + time.asctime(time.localtime(toc)) + '\n')
        print(e, file=joblog)
        joblog.close()
        return 1

    return 0

# ---------------------------------------------------------------

if __name__ == '__main__':

    # Get subjects
    df_subj = pd.read_csv(os.path.join(rootdir,'scripts','subj_info.csv'))
    subjs = df_subj.subj

    # Iterate subjects
    print('Starting parallel jobs...')
    res = Parallel(n_jobs=10) (delayed(getROItcs) (subj) for subj in subjs)

    df = pd.DataFrame()
    df['subj'] = subjs
    df['fail'] = res

    print(df)
    print('All done.')
