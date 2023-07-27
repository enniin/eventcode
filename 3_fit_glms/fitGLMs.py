#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
fitting all the GLMs

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-15
@notes:   checked fitPerms
"""

import os
import pandas as pd
import numpy as np
from statsmodels.api import OLS

# Global locations
rootdir = '/m/nbe/scratch/alex/private/jenni/eventseg'
savedir = os.path.join(rootdir, 'fmri-data','ini-roi')
dmdir = os.path.join(rootdir, 'scripts/2_make_design_matrices/out')

# Basic fitting of bounds and perms -- CHECKED
def fitPerms(df_roi, joblog, dmfile, permfile, areas=None):

    dmpath = os.path.join(dmdir,dmfile)
    permpath = os.path.join(dmdir,permfile)

    df_dm = pd.read_csv(dmpath, index_col=0)
    df_perms = pd.read_csv(permpath, index_col=0)
    
    # DM with constants (wide)
    X = pd.get_dummies(df_dm, columns=['constant'], prefix='run')

    # DF for all betas
    df_betas = pd.DataFrame(columns=['perm','beta','se','p','area'])
    
    if areas is None:
        areas = df_roi.columns[:-1]
    
    # Loop thru areas, gather betas and append to df
    for area in areas:

        # This area = y
        joblog.write('Fitting GLMs for ' + area + '...\n')
        y = df_roi[area]
        X['bound'] = df_dm['bound'] # restore original bounds
        res = OLS(y, X).fit()

        # Save betas from bounds
        betas = pd.DataFrame(columns=['perm','beta','p','se','area'])
        betas = betas.append({'perm':0,
                              'beta':res.params[0],
                              'se':res.bse[0],
                              'p':res.pvalues[0]}, ignore_index=True)

        # Save betas from perms
        for c in df_perms.columns[:-1]:
            X['bound'] = df_perms[c]
            res = OLS(y, X).fit()
            betas = betas.append({'perm': int(c)+1,
                                  'beta':res.params[0],
                                  'se':res.bse[0],
                                  'p':res.pvalues[0]}, ignore_index=True)

        # Append to df
        betas['area'] = area
        df_betas = df_betas.append(betas, ignore_index=True)

        joblog.write('Done.\n')
        
    if df_betas.isnull().values.any():
        joblog.write('ERROR: Resulted in nans. Aborting.\n')
        raise Exception('ERROR: Resulted in nans, no betas returned.')

    return df_betas

# Fit bounds and controls, take contrast as well
def fitControl(df_roi, joblog, dmfile, areas=None):

    dmpath = os.path.join(dmdir,dmfile)
    df_dm = pd.read_csv(dmpath, index_col=0)
    
    # DM with constants (wide)
    X = pd.get_dummies(df_dm, columns=['constant'], prefix='run')
    contrast = np.zeros(X.shape[1])
    contrast[X.columns.get_loc('bound')] = 1
    contrast[X.columns.get_loc('control')] = -1
    
    joblog.write(f'Contrast is {contrast}, with columns {X.columns}.\n')

    # DF for all betas
    df_betas = pd.DataFrame(columns=['area','bound_beta','bound_se',
                                     'control_beta','control_se','t','p'])
    
    if areas is None:
        areas = df_roi.columns[:-1]
    
    # Loop thru areas, gather betas and append to df
    for area in areas:

        # This area = y
        joblog.write('Fitting GLMs for ' + area + '...\n')
        y = df_roi[area]
        res = OLS(y, X).fit()
        t_score = res.t_test(contrast)

        # Save betas from bounds
        betas = pd.DataFrame(columns=['area','bound_beta','bound_se',
                                     'control_beta','control_se','t','p'])
        betas = betas.append({'area':area,
                              'bound_beta':res.params['bound'],
                              'bound_se':res.bse['bound'],
                              'control_beta':res.params['control'],
                              'control_se':res.bse['control'],
                              't':t_score.tvalue.item(),
                              'p':t_score.pvalue.item() }, ignore_index=True)
        # I wonder... am I gonna need all the dfs and stuff later on?
        
        # Append to df
        df_betas = df_betas.append(betas, ignore_index=True)

        joblog.write('Done.\n')
    
    if df_betas.isnull().values.any():
        joblog.write('ERROR: Resulted in nans. Aborting.\n')
        raise Exception('ERROR: Resulted in nans, no betas returned.')
    
    return df_betas

# Fitting N FIRs -- CHECKED
def fitFIR(df_roi, joblog, dmprefix, conds, areas=None):
    
    if areas is None:
        areas = df_roi.columns[:-1]
    
    # DF for all betas
    df_betas = pd.DataFrame(columns=['regressor','beta','se','cond','area'])
    
    for cond in conds:
        dmfile = f'{dmprefix}_{cond}.csv'
        joblog.write('Fitting GLMs for ' + dmfile + '...\n')
        
        dmpath = os.path.join(dmdir,dmfile)    
        df_dm = pd.read_csv(dmpath, index_col=0)
        
        # Design matrix (with dummy constants)
        X = pd.get_dummies(df_dm, columns=['constant'], prefix='run')
        
        # Loop thru areas, gather betas and append to df
        for area in areas:
            betas = pd.DataFrame()
    
            # This area = y
            y = df_roi[area]
            res = OLS(y, X).fit()
            
            # Define which regressors we want
            inds_regs = res.params.index.str.contains('delay')
            betas['regressor'] = res.params.index[inds_regs]
    
            # Save betas from FIR
            betas['beta'] = res.params[inds_regs].to_numpy()
            betas['se'] = res.bse[inds_regs].to_numpy()
            betas['area'] = area
            betas['cond'] = cond
            df_betas = df_betas.append(betas, ignore_index=True)
            
        joblog.write('Done.\n')
    
    if df_betas.isnull().values.any():
        joblog.write('ERROR: Resulted in nans. Aborting.\n')
        raise Exception('ERROR: Resulted in nans, no betas returned.')
    
    return df_betas

# Fitting audio envelope
def fitAudio(df_roi, joblog, dmfile, areas=None,):
    
    # DF for all betas
    df_betas = pd.DataFrame(columns=['beta','se','p','area'])

    joblog.write('Fitting GLMs for ' + dmfile + '...\n')
    
    dmpath = os.path.join(dmdir,dmfile)    
    df_dm = pd.read_csv(dmpath, index_col=0)
    
    # Constants from long to wide
    X = pd.get_dummies(df_dm, columns=['constant'], prefix='run')
    
    if areas is None:
        areas = df_roi.columns[:-1]
    
    # Loop thru areas, gather betas and append to df
    for area in areas:
        
        y = df_roi[area]
        res = OLS(y, X).fit()

        # Save
        betas = dict()
        betas['beta'] = res.params[0]
        betas['se'] = res.bse[0]
        betas['p'] = res.pvalues[0]
        betas['area'] = area
        df_betas = df_betas.append(betas, ignore_index=True)
        
    joblog.write('Done.\n')
    
    if df_betas.isnull().values.any():
        joblog.write('WARNING: Resulted in nans, no betas returned.\n')
        raise RuntimeWarning()
    
    return df_betas

# Fit beta series -- CHECKED
def fitBS(df_roi, joblog, dmfile, areas=None):
    
    # DF for all betas
    df_betas = pd.DataFrame(columns=['area','bound','beta','se','p'])

    joblog.write('Fitting GLMs for ' + dmfile + '...\n')
    
    # Get design matrix
    dmpath = os.path.join(dmdir,dmfile)    
    df_dm = pd.read_csv(dmpath, index_col=0)
    
    # Constants from long to wide
    X = pd.get_dummies(df_dm, columns=['constant'], prefix='run')
    
    # Select boundary regressors
    bound_inds = X.columns.str.isdigit() # bound regressors are numerical
    
    if areas is None:
        areas = df_roi.columns[:-1]
    
    # Loop thru areas, gather betas and append to df
    for area in areas:
        
        y = df_roi[area]
        res = OLS(y, X).fit()

        # Save betas for each bound
        betas = pd.DataFrame()
        betas['bound'] = X.columns[bound_inds].values
        betas['area'] = area
        betas['beta'] = res.params[bound_inds].to_numpy()
        betas['se'] = res.bse[bound_inds].to_numpy()
        betas['p'] = res.pvalues[bound_inds].to_numpy()
        df_betas = df_betas.append(betas, ignore_index=True)
        
    joblog.write('Done.\n')
    
    if df_betas.isnull().values.any():
        joblog.write('ERROR: Resulted in nans. Aborting.\n')
        raise Exception('ERROR: Resulted in nans, no betas returned.')
    
    return df_betas

