#!/bin/bash

#SBATCH --array=0-19 --mem=20000 --time=05:30:00 --output results/slimfair_expe_1/%a.out --error error/slimfair_expe_1/%a.err

python main.py expe/config/slimfair_expe_1/${SLURM_ARRAY_TASK_ID}.txt