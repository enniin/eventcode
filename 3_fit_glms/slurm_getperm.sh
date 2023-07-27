#!/bin/bash
#SBATCH --job-name=getBoundsPerms
#SBATCH --cpus-per-task=10
#SBATCH --output=/m/nbe/scratch/alex/private/jenni/eventseg/scripts/logs/job_%j.out
#SBATCH --time=01:30:00
#SBATCH --mem-per-cpu=200

# Job step
module load anaconda
source activate /m/nbe/scratch/alex/private/jenni/eventseg/evseg_env

srun python3 getAudioPerms.py 3s
