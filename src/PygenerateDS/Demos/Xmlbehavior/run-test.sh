#!/bin/bash

if [ $# -ne 1 ]; then
    echo
    echo Usage: run-test.sh out_file_name_stem
    echo
    exit 0
fi

python ../../generateDS.py \
    -f \
    -o $1sup.py \
    -s $1sub.py \
    --super="$1sup" \
    -b xmlbehavior_po.xml \
    po.xsd
