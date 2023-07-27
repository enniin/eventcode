#!/bin/bash
#SBATCH --job-name=getAVGperms
#SBATCH --cpus-per-task=3
#SBATCH --output=/m/nbe/scratch/alex/private/jenni/eventseg/scripts/logs/job_%j.out
#SBATCH --time=01:30:00
#SBATCH --mem-per-cpu=500M

# Job step
module load anaconda
source activate /m/nbe/scratch/alex/private/jenni/eventseg/evseg_env

srun python3 getAVGaudio.py 3s
