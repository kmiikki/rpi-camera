#!/bin/bash
# SubDirectories Files

find . -type f | cut -d "/" -f2 | uniq -c


