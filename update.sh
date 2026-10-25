#!/bin/bash

cd /srv/hackeropuit.nl/hackeropuit
git -C /srv/hackeropuit.nl/hackeropuit pull && ~/.venv/bin/python3 ./update-events.py && ~/.venv/bin/python3 ./update-website.py
