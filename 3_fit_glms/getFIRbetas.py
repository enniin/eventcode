#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Fit FIR GLMs

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@notes:   Fixing the fMRI timing issue & new react time
"""

from sys import argv
import os
import time
from joblib import Parallel, delayed
import pandas as pd

from fitGLMs import fitFIR

# Global locations and files
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
savedir = os.path.join(rootdir, 'fmri-data','ini-roi')
roifile = 'tc_hoahc_concat.csv'
conds = ['low','mid','high','all']

# =============================================================================
#
# =============================================================================

def getFIRbetas(subj,dmprefix,savefile):
    tic = time.time() # Start

    savepath = os.path.join(savedir,subj)
    if not os.path.isdir(savepath):
        os.makedirs(savepath)

    joblog = open(os.path.join(savepath,'fir_log.txt'), 'w')
    joblog.write('Started '+ subj + ': '+ time.asctime(time.localtime(tic)) + '\n')
    joblog.write('PID: '+ str(os.getpid()) + '\n')

    try:
        # Get ROI tcs
        roipath = os.path.join(savepath,roifile)
        df_roi = pd.read_csv(roipath, index_col=0)
        joblog.write('Loaded '+ roipath + '\n')

        # Fit GLMs for FIR
        df_betas = fitFIR(df_roi, joblog, dmprefix, conds=conds)

        df_betas.to_csv(os.path.join(savepath, savefile))

        toc = time.time() # End
        joblog.write('Ended: '+ time.asctime(time.localtime(toc)) + '\n')
        joblog.close()

    except Exception as e:
        toc = time.time() # End
        joblog.write('Error occured:' + time.asctime(time.localtime(toc)) + '\n')
        print(e, file=joblog)
        joblog.close()
        return 1

    return 0

# ---------------------------------------------------------------

if __name__ == '__main__':
    
    assert len(argv) == 2
    react_time = argv[1]
    
    # Files
    dmprefix = f'dm_fir_{react_time}'
    savefile = f'betas_fir_{react_time}.csv'

    # Get subjects
    df_subj = pd.read_csv(os.path.join(rootdir,'scripts','subj_info.csv'))
    subjs = df_subj.subj

    # Iterate subjects
    print('Starting parallel jobs...')
    res = Parallel(n_jobs=2) (delayed(getFIRbetas) (subj,dmprefix,savefile) for subj in subjs)

    df = pd.DataFrame()
    df['subj'] = subjs
    df['fail'] = res

    print(df)
    print('All done.')
