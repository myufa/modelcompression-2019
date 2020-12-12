#!/bin/bash
#SBATCH --job-name=gate-training-pruning
#SBATCH --account=robosub_team
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --time=1410:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --mail-type=ALL
source venv/bin/activate
python prune.py --config YOLOv3 --epochs 160 --batch-size 16 --save-model
