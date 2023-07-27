#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Gather betas and calc basic average

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@notes:   Fix fMRI timing and new react time
"""

from sys import argv
import os
import time
from joblib import Parallel, delayed
import pandas as pd
from math import sqrt

# Global locations
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
dataroot = os.path.join(rootdir, 'fmri-data/ini-roi')
outdir = os.path.join(rootdir, 'scripts/4_get_averages/out')

subsets = {'all': '',
           '1st': 'listening == "first"',
           '2nd': 'listening == "second"'}

def getAVGperms(key, subjs, betafile,avgfile,longfile):

    tic = time.time() # Start
    pid = str(os.getpid())
    joblog = open(os.path.join(rootdir,'scripts/logs', f'job_log_{pid}.txt'), 'w')
    joblog.write(f'Started: {time.asctime(time.localtime(tic))}\n')
    joblog.write(f'PID: {str(os.getpid())}\n')

    try:
        #  ------------ Get subject files ----------
        df_all = pd.DataFrame()
        try:
            for s in subjs:
                df_this = pd.read_csv(os.path.join(dataroot, s, betafile),index_col=0)
                df_this['subj'] = s
                df_all = df_all.append(df_this, ignore_index=True)
        except FileNotFoundError as e:
            toc = time.time() # End
            joblog.write('Missing file! \n')
            joblog.write('Error occured:' + time.asctime(time.localtime(toc)) + '\n')
            print(e, file=joblog)
            joblog.close()
            return 1

        # Save longfile (only for all subjects and only for intact bounds)
        if key == 'all':
            df_all.query('perm == 0').to_csv(os.path.join(outdir, longfile))

        #  ---------------- Calc AVG --------------
        df_avg = pd.DataFrame()
        areas = df_all.area.unique()
        perms = df_all.perm.unique()

        # do areas
        for a in areas:
            # do perms
            for p in perms:
                these = df_all.query('perm == @p & area == @a & subj in @subjs')
                avg = these['beta'].mean()
                se = these['beta'].std()/sqrt(len(these)) # SEM
                this = {'perm': p,
                        'beta': avg,
                        'se': se,
                        'area': a}
                df_avg = df_avg.append(this, ignore_index=True)

        savefile = f'{avgfile}_{key}.csv'
        df_avg.to_csv(os.path.join(outdir, savefile))

        toc = time.time() # End
        joblog.write('Saved: '+ savefile + '\n')
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
    betafile = f'betas_boundperm_{react_time}.csv'
    avgfile = f'AVG_boundperms_{react_time}'
    longfile = f'betas_boundperms_long_{react_time}.csv'

    # Get subjects
    df_subj = pd.read_csv(os.path.join(rootdir,'scripts','subj_info.csv'))

    print('Getting AVGs for:')
    subjsets = dict()
    for (key, expr) in subsets.items():
        if key == 'all':
            subjsets[key] = df_subj.subj
            print(key + ', nsubj: '+ str(subjsets[key].count()))
        else:
            subjsets[key] = df_subj.query(subsets[key]).subj
            print(key + ', nsubj: '+ str(subjsets[key].count()))


    # Iterate subject sets (3)
    print('Starting parallel jobs...')
    res = Parallel(n_jobs=3) (delayed(getAVGperms) (key,subjs,betafile,avgfile,longfile) for (key,subjs) in subjsets.items())

    df = pd.DataFrame()
    df['subj'] = list(subsets.keys())
    df['fail'] = res

    print(df)

    print('All done.')
