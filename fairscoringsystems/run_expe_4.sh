#!/bin/bash

#SBATCH --array=0-59 --mem=20000 --time=05:30:00 --output expe/results/expe_4/%a.out --error error/expe_4/%a.err

python main.py expe/config/expe_4/${SLURM_ARRAY_TASK_ID}.txt