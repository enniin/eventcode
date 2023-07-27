#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Gather betas for beta series
NOTE: for the linear model we don't need averages, so we just save the longfile

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-18
@notes:   Fix fMRI timing and new react time
"""

from sys import argv
import os
import pandas as pd

dataroot = '/m/nbe/scratch/alex/private/jenni/eventseg/fmri-data/ini-roi'
scriptroot = '/m/nbe/scratch/alex/private/jenni/eventseg/scripts'
outdir = os.path.join(scriptroot, '4_get_averages/out')

def runAVGseries(betafile,longfile):
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
    print('Saved longfile. Done.')


if __name__ == '__main__':

    assert len(argv) == 2
    react_time = argv[1]

    betafile = f'betas_series_{react_time}.csv'
    longfile = f'betas_series_long_{react_time}.csv'

    runAVGseries(betafile,longfile)
