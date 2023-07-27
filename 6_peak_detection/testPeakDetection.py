#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 30 11:10:51 2021

@author: jenska
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

dataroot = '/Users/jenska/code/python/eventcode'
indir = os.path.join(dataroot,'1_create_boundaries/out')
boundfile = 'boundaries_f3s.csv'
permfile = 'perms_f3s.npy'

# average signal across participants (save and load)

# Get boundaries and parts
df_bounds = pd.read_csv(os.path.join(indir,boundfile),index_col=0)
df_parts = pd.read_csv(os.path.join(indir,'partlensf.csv'),index_col=0)

# Niter = Nbounds
# get parts
# NTR = len(sum(parts.len))
# create TR pool

Niter = len(df_bounds)
NTR = df_parts.flen.sum()


#%% Randomly select some TRs

TRpool = np.ones(NTR)
for i in range(Niter):
    
    # get available TRs
    inds = np.nonzero(TRpool)[0]
    #print(len(inds))
    
    # for each TR:
        # create DM with trigger at this TR
        # fit to data
        # collect RSS of model
    # select TR with lowest RSS (beta>0, no-flip)
    
    selTR = np.random.choice(inds)
    
    # add TR to model and remove from pool
    TRpool[selTR] = 0

# Define trigger model
model = np.nonzero(TRpool == 0)[0]
print(model)
# Save the model

del(inds,selTR)
#%% Test fit

# get perms
perms = np.load(os.path.join(indir, permfile))
matches = np.zeros((Niter,1001))

# Test model fit with permutations (± 2 sec)
win = 2
for i_perm in range(perms.shape[1]):
    perm = perms[:,i_perm]
    
    # Compare each trigger in the model to this perm
    for i_trig in range(len(model)):
        trigger = model[i_trig]
        diff = perm - trigger
        # if there's a close enough match, mark the trigger as matched
        if len(np.nonzero(abs(diff) < win)[0]):
            matches[i_trig,i_perm] = 1

# Finally do the same for intact boundaries
i_perm = matches.shape[1]-1   # use the last column
perm = df_bounds.frt_concat.to_numpy()
for i_trig in range(len(model)):
        trigger = model[i_trig]
        diff = perm - trigger
        # if there's a close enough match, mark the trigger as matched
        if len(np.nonzero(abs(diff) < win)[0]):
            matches[i_trig,i_perm] = 1

# Get match proportions for all
match_prop = matches.sum(axis=0)/matches.shape[0]
# Save these results

# Calc significance as proportion of perms > bounds
match_bounds = match_prop[-1]
perm_inds = np.nonzero( match_prop[:-1] >  match_bounds)[0]
sig = len(perm_inds) / (len(match_prop)-1)

print(sig)
print(match_prop.mean())
print(match_bounds)
plt.hist(match_prop)

# With randomly selected TRs this should not be significant, and it isn't

del(perm,trigger,diff,i_trig,i_perm)
#%%