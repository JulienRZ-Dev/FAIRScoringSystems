#!/bin/bash

#SBATCH --array=0-19 --mem=20000 --time=05:30:00 --output expe/results/expe_1/%a.out --error error/expe_1/%a.err

python main.py expe/config/expe_1/${SLURM_ARRAY_TASK_ID}.txt 