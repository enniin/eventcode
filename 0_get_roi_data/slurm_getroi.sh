#!/bin/bash
#SBATCH --job-name=getROItcs
#SBATCH --cpus-per-task=10
#SBATCH --output=/m/nbe/scratch/alex/private/jenni/eventseg/scripts/logs/job_%j.out
#SBATCH --time=01:00:00
#SBATCH --mem-per-cpu=700

# Job step
module load anaconda3
source activate /m/nbe/scratch/alex/private/jenni/eventseg/evseg_env

srun python3 getROItcs.py
