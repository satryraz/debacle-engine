#!/bin/bash

python3 -m nuitka --onefile --standalone --lto=yes --output-filename=debacle-engine main.py

if [ $? -eq 0 ]; then
    echo "---------------------------------------"
    echo "Compilation réussie : ./debacle-engine"
    echo "---------------------------------------"
else
    echo "Erreur lors de la compilation."
fi
