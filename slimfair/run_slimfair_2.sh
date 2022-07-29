#!/bin/bash

#SBATCH --array=0-59 --mem=20000 --time=05:30:00 --output results/slimfair_expe_2/%a.out --error error/slimfair_expe_2/%a.err

python main.py expe/config/slimfair_expe_2/${SLURM_ARRAY_TASK_ID}.txt