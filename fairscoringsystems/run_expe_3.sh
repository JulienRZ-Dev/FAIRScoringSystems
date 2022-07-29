#!/bin/bash

#SBATCH --array=0-119 --mem=20000 --time=05:30:00 --output expe/results/expe_3/%a.out --error error/expe_3/%a.err

python main.py expe/config/expe_3/${SLURM_ARRAY_TASK_ID}.txt