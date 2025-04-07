#!/bin/bash
cd /home/n1x9s/viewTrain
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart viewtrain
