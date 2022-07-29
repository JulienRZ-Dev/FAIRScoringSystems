#!/bin/bash

#SBATCH --array=0-9 --mem=20000 --time=05:30:00 --output expe/results/expe_2/%a.out --error error/expe_2/%a.err

python main.py expe/config/expe_2/${SLURM_ARRAY_TASK_ID}.txt