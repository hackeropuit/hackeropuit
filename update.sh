#!/bin/bash

cd /home/hackeropuit/site/
git -C /home/hackeropuit/site/ pull && ./update-events.py && ./update-website.py
