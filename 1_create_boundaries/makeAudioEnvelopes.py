#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENTSEGMENTATION helper
Calculating and saving the envelopes

@author: saarisj2
"""
from os.path import join
from time import time
import gc
import resource
import numpy as np

from scipy.io.wavfile import read
from scipy.signal import hilbert, decimate

audiodir = '/m/nbe/scratch/alex/stimuli/wav/concatenated_story'

# For tracking mem usage
def mem_use():
    muse = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 0)
    print(f'Memory usage:  {muse} MB')
mem_use()

#%% To battle memory leaks we have to define a generator for the actual work
# Not that it helps, really...

gc.set_threshold(100)

def save_envelope(parts, d):
    audio = []
    envelope = []
    denv = []
    
    for p in parts:
        print(f'Extracting part {p}...')
        srate, audio = read(join(audiodir, f'kappale{p}.wav'))
        print(f'Length of part: {len(audio)/srate/60} min')
        
        # Extract and decimate envelope to 10Hz
        tic = time()
        envelope = np.array(abs(hilbert(audio)))
        denv = np.array(decimate(envelope, round(srate/d), ftype='fir'))
        mem_use()
        print(gc.get_count())
        
        # Save
        fname = f'kappale{p}_envelope_{d}Hz.npy'
        np.save(join(audiodir, fname), denv, allow_pickle=False)
        print(f'Saved envelope as {fname}.')
        
        toc = time()
        print(f'Took {toc-tic} seconds.\n')
        
        yield 0

#%% Exctract and save envelopes
# In parts, as there's still some memory leak I can't pinpoint :(

d = 10 # final srate of envelope, Hz
part1 = list(range(1,5))
part2 = list(range(5,9))
part3 = list(range(9,11))

mem_use()
re = [r for r in save_envelope(part3, d)]
gc.collect()
mem_use()

#%%