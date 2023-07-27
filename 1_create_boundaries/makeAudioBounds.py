#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION
Make sets of audio gaps with and without bounds to control

@author:  jenni.saaristo@helsinki.fi
@version: 2021-08-26
@notes:   First draft
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#datadir = '/m/nbe/scratch/alex/private/jenni/eventseg/segmentdata'
datadir = '/Users/jenska/code/python/eventcode/1_create_boundaries/out'
boundfile = 'boundaries_f3s_vol.csv'
gapfile = 'all_audiogaps_f.csv'
partfile = 'partlensf.csv'

#%% Get dfs
df_bounds = pd.read_csv(os.path.join(datadir,boundfile), index_col=0)
df_gaps = pd.read_csv(os.path.join(datadir,gapfile), index_col=0)
df_parts = pd.read_csv(os.path.join(datadir,partfile), index_col=0)

#%% Drop the audio gaps that are not sentence boundaries
#   We don't want to have those in either bounds or perms
#   These have been checked from the stimulus manually
bad_inds = [68,95,126,154,161,204]
df_gaps = df_gaps.drop(bad_inds).reset_index(drop=True)
bad_inds = df_bounds.query('id == 999').index          # drop post hoc as well
df_bounds = df_bounds.drop(bad_inds).reset_index(drop=True)

#%% Find out how the bounds look in relation to the gaps

for i in df_gaps.index:
    plt.plot( [df_gaps['off_frt_concat'][i], df_gaps['on_frt_concat'][i]], [0,0], 'b-')
plt.stem(df_bounds['frt_concat'], df_bounds['nobs']-4.5, bottom=-1, linefmt='r', markerfmt='ro')
plt.ylim(-1,20)
plt.show()

# It seems that mostly the bounds are associated with a gap – that's pretty good
# news regarding our reaction time! But now as the bounds have been moved so much,
# we can't be sure that the previous gap is the right one, i.e. we'll have to
# search both directions. How much leeway should we give? I guess we should consider
# the slowness of BOLD response – perhaps ±2 secs is reasonable
#%% Define parameters and find gaps
win = 2

df_bounds['gap_id'] = None
drop_inds = []
for i in df_bounds.index:
    frt = df_bounds['frt_concat'][i]
    
    # largen the gaps with win and see if bound fits inside
    gs = df_gaps.query('off_frt_concat-@win < @frt & @frt < on_frt_concat+@win').index
    if not gs.empty:
        df_bounds.loc[i,'gap_id'] = gs[0]
        
        # for two gaps select the closest one, drop other:
        if len(gs)==2:
            print(f'Two gaps for index {i}')
            d_0 = df_gaps.loc[gs[0],'on_frt_concat'] - frt
            d_1 = frt - df_gaps.loc[gs[1],'off_frt_concat']
            if d_0 < d_1:
                df_bounds.loc[i,'gap_id'] = gs[0]
                drop_inds.append(gs[1])
            else:
                df_bounds.loc[i,'gap_id'] = gs[1]
                drop_inds.append(gs[0])
        
        # this shouldn't happen:
        elif len(gs)>2:
            print(f'Too many gaps! Check index {i}')
                
print(df_bounds[~df_bounds['gap_id'].isna()].count()[0])
print(drop_inds)
del(d_0,d_1,frt,i,gs)
#%% Make boundgaps

# We'll use the middle of the gap as the timing
df_gaps['frt_concat'] = df_gaps['on_frt_concat'] - df_gaps['gap_dur']/2
df_gaps = df_gaps.drop(index=drop_inds)  # don't reset index now!!

gap_inds = df_bounds.query('gap_id == gap_id')['gap_id'].to_numpy(dtype='int') # filter away Nones
df_gapbound = df_gaps.loc[gap_inds,:].copy()
df_gapother = df_gaps.drop(index=gap_inds) 

print(df_gapbound['gap_dur'].mean())
print(df_gapbound['gap_dur'].std())
print(df_gapother['gap_dur'].mean())
print(df_gapother['gap_dur'].std())

#%% Save the bounds
df_gapbound.to_csv(os.path.join(datadir,'audiobounds_f3s.csv'))

#%% Create permgaps
# Randomly sample same amount of non-bound gaps for 1000 sets, segment len > 6
# Would've liked to use seglen=10, but that gets pretty tricky

# Sample the gaps
nbound = len(df_gapbound)
nperm = 1000
seglen = 6
arr_sample = np.zeros([nbound,nperm])

i = 0
k = 0
while i < nperm:
    sample = df_gapother.sample(nbound)
    sample.sort_index(inplace=True)
    if sample['frt_concat'].diff().abs().min() > seglen:
        arr_sample[:,i] = sample['frt_concat']
        i = i+1
    k = k+1

print(k)

#%% Do we have identical perms
from scipy.spatial.distance import pdist, squareform
p = squareform(pdist(arr_sample.T))
plt.imshow(p)
plt.colorbar()
print(len(p[p == 0]))

# No doesn't look like it!
# I'll skip further stats on these – let's just report the overall mean/sd

#%% Save the perms
np.save(os.path.join(datadir,'audioperms_f3s.npy'), arr_sample, allow_pickle=False)


#%% Print to check individual bounds against stimulus
def sec2tc(sec):
    return f'{int(sec/60)}:{sec%60}'

tcs = [ sec2tc(sec) for sec in df_gapbound.audio_off ]
print(tcs)



#%%
