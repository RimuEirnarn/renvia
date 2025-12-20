#!/usr/bin/env bash

printf "Activating virtual environment...\n"
python -m venv .venv
source .venv/bin/activate

printf "Installing from requirements.\n"
pip install -r ./requirements.txt
chmod +x main.py

printf "Setup complete\n"
