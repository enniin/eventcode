#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION HELPER FUNCTIONS
jenni.saaristo@helsinki.fi

@ plot_to_sound()
plot with audio
inputs:    ax - axis to plot on
           dfs - array of dataframes to plot
           sound - audio data
           fs - sampling freq of audio
           labels - labels of dfs
           title - title
           legend - to show or not

@ plot_no_sound()
plot without audio
inputs:
           dfs - array of dataframes to plot
           partlen - duration of part in secs
           labels - labels of dfs (default None)
           title - title
           legend - to show or not
           gaps - optional audio gaps to plot
           ax - optional axis to plot on
           maxplus - how much to add to maxcount (default=5)

"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import pandas as pd
from math import trunc

# Plot with audio

def plot_to_sound(ax, dfs, sound, fs, labels, title='default title', legend=False):

    secticks = lambda x, pos : trunc(x/fs)%60
    minticks = lambda x, pos : trunc(x/fs/60)

    colors = ['xkcd:dusty rose','xkcd:dark magenta','xkcd:moss','xkcd:pine green']

    ax.plot(sound/10, linewidth=0.5, color='xkcd:light gray')

    for (i,df) in enumerate(dfs):
        x = df['rt']*fs
        y = np.ones(len(df))*(1000*i)
        s = df['nobs']*20
        ax.scatter(x, y, s, c=colors[i], label=labels[i], zorder=3)

    if legend:
        ax.legend(loc='upper center', ncol=2, fontsize=8, handletextpad=0.5)

    ax.set_xlabel('time')
    ax.set_title(title)

    ax.set_xlim(0,len(sound))
    ax.tick_params(axis="x", which='minor', labelsize=6)

    ax.yaxis.set_major_locator(plt.NullLocator())
    ax.xaxis.set_major_locator(plt.MultipleLocator(fs*60))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(fs*10))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(minticks))
    ax.xaxis.set_minor_formatter(plt.FuncFormatter(secticks))

    return ax

# plot without audio
def plot_no_sound(dfs, partlen, labels=None, title='default title', legend=False,
                  gaps=None, ax=None, maxplus=7):
    '''
    Plot boundaries without waveform, but with optional audio gap markers.

    Parameters
    ----------
    dfs : DataFrame or list of DataFrames
        The boundaries.
    partlen : int
        Length of the part in seconds.
    labels : list of str, optional
        Labels to give to the boundary sets. The default is [''].
    title : str, optional
        Title of the plot. The default is 'default title'.
    legend : boolean, optional
        Whether or not to include legend. The default is False.
    gaps : DataFrame, optional
        A dataframe giving the onset and duration of audio gaps. The default is None.
    ax : Axis, optional
        Optional axis to plot the figure to. The default is None.
    maxplus : int, optional
        How much to add to the y on top of max value. The default is 5.

    Returns
    -------
    ax : Axis
        Axis containing the plot.

    '''
    secticks = lambda x, pos : trunc(x)%60
    minticks = lambda x, pos : trunc(x/60)

    #colors = ['xkcd:dusty rose','xkcd:dark magenta','xkcd:moss','xkcd:pine green']
    
    if type(dfs) is pd.core.frame.DataFrame:
        dfs = [dfs]
    if ax is None:
        fig, ax = plt.subplots()
    if labels is None:
        labels = [str(i+1) for i in range(len(dfs))]

    maxcount = 0
    for (i,df) in enumerate(dfs):
        x = df['rt']
        y = df['nobs']+0.2*i
        s = df['nobs']*14
        ax.scatter(x, y, s, label=labels[i], zorder=3)
        for (xi,yi) in zip(x,y):
            ax.plot([xi,xi],[0,yi],color='xkcd:light gray',linestyle='-', zorder=2)
        maxcount = maxcount if maxcount > max(df['nobs']) else max(df['nobs'])

    if gaps is not None:
        gapboxes = [ Rectangle((x,0), w, 2) for (x,w) in zip(gaps.onset, gaps.dur)]
        pc = PatchCollection(gapboxes, facecolor='orange')
        ax.add_collection(pc)


    if legend:
        ax.legend(loc='upper center', ncol=len(labels), fontsize=7, handletextpad=0.5)

    ax.set_xlabel('time')
    ax.set_title(title)

    ax.set_ylim(0,maxcount+maxplus)
    ax.set_xlim(0,partlen)
    ax.tick_params(axis="x", which='minor', labelsize=6)

    #ax.yaxis.set_major_locator(plt.NullLocator())
    ax.xaxis.set_major_locator(plt.MultipleLocator(60))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(10))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(minticks))
    ax.xaxis.set_minor_formatter(plt.FuncFormatter(secticks))

    return ax

"""little helper to massage the axs list to have correct length..."""
def trim_axs(axs, N):
    axs = axs.flat
    for ax in axs[N:]:
        ax.remove()
    return axs[:N]