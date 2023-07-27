# Event segmentation analysis pipeline

ROI analyses on the ALEX fMRI data. Main analyses are the comparison of responses to intact boundary set vs. its permutations (_bounds vs. perms_), FIR models for plotting (_FIR plotting_), testing salience modulation with a beta series approach (_salience modulation_), and exploring responses to adjusted boundary timings (_boundary timings_). These scripts deal with the extraction of ROIs and fitting of the various glms – the actual statistical tests and plotting are done in a separate R markdown file (see folder 5_analyses_plots).

The folders are organised according to phase, not analysis:
* 0: Extract and save the ROI averaged data
* 1: Create the combined boundary set from behavioral annotations
* 2: Make design matrices for the different analyses
* 3: Fit the GLMs (generally heavy lifting, requires HPC/slurm)
* 4: Get the averages over subjects (partially heavy lifting)
* 5: Statistical analyses and plotting

The script `fitGLMs.py` contains the real work horses, i.e. the functions that fit the actual GLMs.

Note: the `get` scripts are meant to be run with slurm – they require intense computations. Their attendant sbatch scripts are also included in the repo. The `run` and `make` scripts on the other hand are meant to be run on Spyder (or some other IDE).

### Extraction of ROI time courses

`makeHCmask.py` : creates the hippocampal mask from HOA subcortical
    > hipp_thr25_2mm.nii

`getROItcs.py` : extracts the timecourses, detrends and zscores, and concatenates all the runs
    > **tc_hoahc_concat.csv**

### Creating the behavioral boundary sets

`evseg` : The evseg package, which includes functions to chain-combine the behavioral annotations and plot results in stimulus time. This is an adaptation of the method used in Ben-Yakov and Henson (2018).

`makeBoundaries.py` : Combines the behavioral annotations based on descriptive statistics from the annotation data -- essentially trying to retain the same average number of boundaries with reasonable length of segments and clusters. See the thesis for elaboration on this issue.
    > boundaries_f_20210613.csv

`makePermuted.py` : Makes 1000 permutation sets from the boundaries by shuffling their segment lengths. Saved perms are in the correct concatenated fMRI timeframe (smoothing lag and tail signal accounted for).
    > perms_f_20210815.csv

`makeAudioGaps.py` : Calculates the fMRI times for all speech gaps with dur > 1 second.
    > all_audiogaps_f.csv

### Bounds vs perms

`makeDMboundperms.py` : makes the design matrices for intact and permuted boundaries
    > dm_bounds.csv & dm_perms.csv

`getBoundsPerms.py` : runs the glm on all subjects and all areas, both bounds and permutations (total of 1001 glms) -- quite heavy lifting
    > betas_boundperms.csv

`getAVG.py` : collects the betas from all participants and saves both a longfile and averages
    > **AVG_boundperms_{group}.csv** & **betas_boundperms_long.csv**

`plotBrainResults.py` : takes the ROI results (from R) and creates brain plots

### FIR plotting

`makeDMfir.py` : makes the design matrices for FIR plotting, each salience level separately
    > dm_fir_{level}.csv

`getFIRbetas.py` : runs all 3 glms on all subjects and areas -- NOTE: does not require slurm, can be run from command line
    > betas_fir.csv

`runAVGfir.py` : save longfiles and calculate averages (interactively or from command line)
    > **AVG_fir_{group}.csv** & **betas_fir_long.csv**

### Salience modulation

`makeDMbetaseries.py` : makes the design matrix with one regressor for each event boundary
    > dm_series.csv

`getBetaSeries.py` : runs the glm on all subjs and areas -- NOTE: this doesn't require slurm, as this is in fact quite light. You can run it directly from command line, after loading anaconda and the evseg environment (takes maybe couple of mins)
    > betas_series.csv

`runAVGseries.py` : gathers betas to the longfile -- no averaging, as the analyses don't require those
    > **betas_series_long.csv**

### Exploratory boundary timings

`makeAudioBounds.py` : relocates the high salience boundaries to audio gaps, and also creates the random sham sets
    > bounds_audioevents.csv & bounds_audioperms_onset.csv & bounds_audioperms_offset

`makeDMaudevents.py` : creates the design matrices for the actual events and the sham sets (perms) for audio offsets and onsets
    > dm_audioevents_{cond]}.csv & dm_audioperm_{cond}.csv

`getAudioPermBetas.py` : runs glms on events and perms for both audio gap conditions (audio on, audio off) -- very heavy lifting
    > betas_audioevent_{cond}.csv

`getAVGaudioev` : calculates averages and saves longfile (only for intact boundaries)
    > **AVG_audev_{cond}_{grp}.csv** &  **betas_audev_long_{cond}.csv**

### Plot exploratory boundaries

`makeDMaudevFIR.py` : creates the FIR design matrices
`getFIRaudev.py` : runs the glms -- NOTE: does not require slurm, light computation (can be run on VDI)
`runAVGfiraudev.py` : calc and save averages and longfile

`makeDMaudevFIRdtrl.py` : creates FIR design matrices for a random control set
`getFIRaudctrl.py` : runs the glms -- NOTE: does not require slurm, light computation (can be run on VDI)
`runAVGfiraudev.py` : calc and save averages and longfile
