#!/bin/bash

. ~/.venv/bin/activate
cd /srv/hackeropuit.nl/hackeropuit
git -C /srv/hackeropuit.nl/hackeropuit pull && ./update-events.py && ./update-website.py
