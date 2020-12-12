#!/bin/bash
#SBATCH --job-name=model_compression
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
python prune.py --config YOLOv3 --pretrained-weights YOLOv3-prune-perc-29.866345702343708.pt --save-model --batch-size 16 --start-at-prune-rate 30
