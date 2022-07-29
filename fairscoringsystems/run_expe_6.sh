#!/bin/bash

#SBATCH --array=0-59 --mem=20000 --time=05:30:00 --output expe/results/expe_6/%a.out --error error/expe_6/%a.err

python main.py expe/config/expe_6/${SLURM_ARRAY_TASK_ID}.txt 