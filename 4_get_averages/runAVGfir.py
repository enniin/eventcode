#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Gather betas and calc basic average for FIR models

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@notes:   Fix fMRI timing and new react time
"""

from sys import argv
import os
import pandas as pd
from math import sqrt

dataroot = '/m/nbe/scratch/alex/private/jenni/eventseg/fmri-data/ini-roi'
scriptroot = '/m/nbe/scratch/alex/private/jenni/eventseg/scripts'
subsets = {'all': '',
           '1st': 'listening == "first"',
           '2nd': 'listening == "second"'}

outdir = os.path.join(scriptroot,'4_get_averages/out')

def runAVGfir(betafile,longfile,savepfix):
    
    # Get subjs
    df_subj = pd.read_csv(os.path.join(scriptroot, 'subj_info.csv'))
    
    # Get data
    df_all = pd.DataFrame()
    for s in df_subj.subj:
        df_this = pd.read_csv(os.path.join(dataroot, s, betafile),index_col=0)
        df_this['subj'] = s
        df_all = df_all.append(df_this, ignore_index=True)
    
    # Save long df
    df_all.to_csv(os.path.join(outdir, longfile))
    print('Saved longfile. Calculating averages...')
    
    # Calc and save
    areas = df_all.area.unique()
    regs = df_all.regressor.unique()
    conds = df_all.cond.unique()
    
    for (key, expr) in subsets.items():
    
        if key == 'all':
            subjs = df_subj.subj
        else:
            subjs = df_subj.query(subsets[key]).subj
        print(f'{key}, nsubj: {str(subjs.count())}')
    
        df_avg = pd.DataFrame()
        # do areas
        for a in areas:
            # do levels
            for c in conds:
                # do delays
                for r in regs:
                    these = df_all.query('regressor == @r & cond == @c & area == @a & subj in @subjs')
                    avg = these['beta'].mean()
                    se = these['beta'].std()/sqrt(len(these))
                    this = {'regressor': r,
                            'beta': avg,
                            'se': se,
                            'cond': c,
                            'area': a}
                    df_avg = df_avg.append(this, ignore_index=True)
        savefile = f'{savepfix}_{key}.csv'
        df_avg.to_csv(os.path.join(outdir, savefile))
        print('Saved '+ savefile)
    
    print('Done.')

if __name__ == '__main__':
    
    assert len(argv) == 2
    react_time = argv[1]
    
    betafile = f'betas_fir_{react_time}.csv'
    longfile = f'betas_fir_long_{react_time}.csv'
    savepfix = f'AVG_fir_{react_time}'
    
    runAVGfir(betafile,longfile,savepfix)
