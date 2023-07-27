#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENT SEGMENTATION HELPER FUNCTIONS


@author:  jenni.saaristo@helsinki.fi
@version: 2021-04-26
@notes:   seglen now deals with ndarrays, removed old chain

"""

import pandas as pd
import numpy as np

def to_concat_rts(df_bounds, df_parts, column='rt'):
    """
    Create concatenated times from part-wise times
    

    Parameters
    ----------
    df_bounds : DataFrame
        Df containing the boundaries.
    df_parts : DataFrame
        Df containg info on parts.
    column : str, optional
        Name of the column to use for rts. The default is 'rt'.

    Returns
    -------
    rt_concat : Series
        The concatenated times.

    """
    rt_concat = pd.Series()
    for i in df_parts.index:
        p = df_parts.part[i]
        ind = df_bounds.query('part == @p').index
        rt_concat = rt_concat.append(df_bounds.loc[ind, column] + df_parts.start[i])
        
    return rt_concat


def chain_concat(dforig, partlens, win1=2, win2=4):

    # ----------------------- FIRST ITER -------------------------
    # Go through all boundaries in the dataset chronologically, marking them
    # as belonging to the same 1st level cluster as long as the difference
    # between consecutive boundaries is less than win1.
    # Also calculate the avg rt of the cluster, together with the number of
    # boundaries, and also the cluster length.
    # Add this info to a copy of the original dataframe.

    df = dforig.copy()
    win = win1

    # new data columns
    cluster = np.zeros(len(df)) # cluster id
    avg_rt = np.zeros(len(df))  # avg rt of cluster
    numb = np.zeros(len(df))    # number of boundaries in cluster
    lenc = np.zeros(len(df))    # length of cluster

    # find and demarcate 1st iter clusters
    i = 0
    c = 1
    while i < len(df):

        # start a new cluster
        cluster[i] = c
        this_rt = df.iloc[i]['rt_concat']
        j = 1

        # look forward for next boundaries
        while True:

            # if next ind doesn't exist, get out of here
            if i+j == len(df):
                avg_rt[i:i+j] = df[i:i+j]['rt_concat'].mean()  # HOX! slicing excludes last ind
                numb[i:i+j] = j
                lenc[i:i+j] = df.iloc[i+j-1]['rt_concat'] - df.iloc[i]['rt_concat']
                i = i+j
                break

            # next ind exists, get its rt
            next_rt = df.iloc[i+j]['rt_concat']

            # next is within (moving) window, add to cluster
            if abs(next_rt - this_rt) < win:
                cluster[i+j] = c
                this_rt = next_rt    # chaining
                j += 1
            # next is further out, break cluster
            else:
                avg_rt[i:i+j] = df[i:i+j]['rt_concat'].mean()  # HOX! slicing excludes last ind
                numb[i:i+j] = j
                lenc[i:i+j] = df.iloc[i+j-1]['rt_concat'] - df.iloc[i]['rt_concat']
                c += 1
                i = i+j
                break

    # add cluster info to df
    df  = df.assign(cluster_id = cluster)
    df  = df.assign(avg_rt = avg_rt)
    df  = df.assign(num_bounds = numb)
    df  = df.assign(cluster_len = lenc)


    # ------------------- SECOND ITER -----------------------------
    # Go through 1st level clusters and compare their avg rts to decide
    # which clusters should merge.
    # First only mark the clusters, then collect the boundaries that might
    # belong to them, check for duplicate presses from subjects and deal with
    # them, and finally calculate values for 2nd level clusters: rts, lengths
    # and saliencies.

    # by default discard clusters with only one boundary at this point
    df1st = df.query('num_bounds > 1')
    df1st = df1st.reset_index(drop=True)

    win = win2

    # dataframe to map 1st level clusters to 2nd level clusters
    cols = ['cluster_id','avg_rt','cluster2_id']
    dfclus = pd.DataFrame(columns=cols, dtype=float)
    dfclus['cluster_id'] = df1st['cluster_id'].unique() # 1st level id
    dfclus['avg_rt'] = df1st['avg_rt'].unique()         # 1st level avg rt

    # mark the 2nd level clusters (not yet averaging)
    i = 0
    c = 1
    while i < len(dfclus):

        # start a new cluster
        dfclus.iloc[i]['cluster2_id'] = c
        this_rt = dfclus.iloc[i]['avg_rt']
        j = 1

        while True:

            # if next ind doesn't exist, get out of here
            if i+j == len(dfclus):
                i = i+j
                break

            # next ind exists, get its rt
            next_rt = dfclus.iloc[i+j]['avg_rt']

            # next is within (moving) window
            if abs(next_rt - this_rt) < win:
                dfclus.iloc[i+j]['cluster2_id'] = c
                this_rt = next_rt    # chaining
                j += 1
            # next is further out, break cluster
            else:
                c += 1
                i = i+j
                break

    # join mapping info with other data ==> data for final averaging
    df2nd = df1st.merge(dfclus, on='cluster_id', how='left', suffixes=('','2'))
    df2nd[['cluster_id','num_bounds','cluster2_id']] = df2nd[['cluster_id','num_bounds','cluster2_id']].astype(int)

    # new empty dataset to hold final combined data
    cols = ['id','part','rt','rt_concat','clen','nobs']
    dffin = pd.DataFrame(columns=cols, dtype=float)

    # go through 2nd level clusters and average into final boundaries
    for i in df2nd['cluster2_id'].unique():

        # get rows for this final cluster
        this_df = df2nd.query('cluster2_id == @i')

        # check for duplicate subjects
        dubs = this_df.duplicated(subset='subj', keep=False)

        # if duplicates exist, average over them
        for s in this_df[dubs]['subj'].unique():
            new_rt = this_df.loc[this_df.subj == s]['rt_concat'].mean()
            inds = this_df.loc[this_df.subj == s].index
            this_df.at[inds[0],'rt_concat'] = new_rt    # new rt to first subj row
            this_df = this_df.drop(index=inds[1:])      # drop the rest

        # TODO: if there are several duplicated subjects, we might have a problem
        # and need to veto the merge!
        
        # Find out into which part the new boundary actually falls
        rt = this_df['rt_concat'].mean()
        p = partlens.query('start < @rt').iloc[-1].part
        
        # save info on final boundary to dffin
        this_row = {}
        this_row['id'] = i
        this_row['part'] = p
        this_row['rt'] = rt - partlens.start[p-1]
        this_row['rt_concat'] = rt
        this_row['clen'] = this_df['rt_concat'].max() - this_df['rt_concat'].min()
        this_row['nobs'] = this_df['subj'].count()
        dffin = dffin.append(this_row, ignore_index=True)

    dffin[['id','part','nobs']] = dffin[['id','part','nobs']].astype(int)

    return [dffin, df2nd]


def to_segments(bounds, len_total, drop=False):
    """
    Convert from boundaries to segment lengths
    
    Calculates length of segments from a list of boundaries and the total
    length of the stimulus. Optionally drops first and last segments.

    Parameters
    ----------
    bounds : Series
        The boundaries.
    len_total : float
        Total lenght.
    drop : bool, optional
        Drop first and last segments or not. The default is False.

    Returns
    -------
    diffs : ndarray
        The segments (segment lengths).

    """
    
    ends = bounds.to_numpy()
    beginnings = ends
    beginnings = np.insert(beginnings, 0, 0) # insert 0 to beginnings
    ends = np.append(ends, len_total)   # append total len to ends
    diffs = ends - beginnings
    
    # We sometimes want to drop the first and last segments
    if drop:
        diffs = diffs[1:-1]
    
    return diffs


def make_permutations(segments, n=1000):
    """
    Make N permutations of given segments

    Parameters
    ----------
    segments : ndarray
        The segments to shuffle.
    n : int, optional
        Number of permutations The default is 1000.

    Returns
    -------
    perms : ndarray
        All permutations (boundaries) as a bounds x N array.

    """
    
    perms = np.zeros([len(segments)-1,n])
    
    for i in range(n):
        np.random.shuffle(segments)
        rts = segments.cumsum()    # boundaries from segments
        perms[:,i] = rts[:-1]
    
    return perms



