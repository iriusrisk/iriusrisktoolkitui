#!/bin/sh -x

if [ $# -ne 1 ]; then
    echo
    echo Usage: run-ful-test.sh out_file_name_stem
    echo
    exit 0
fi

python ../../generateDS.py -f -m \
  --namespacedef='xmlns:pl="http://kuhlman.com/people.xsd"' \
  --super=$1sup -o $1sup.py -s $1sub.py \
  --member-specs=dict \
  -m \
  --export="write etree literal" \
  -c people_catalog.xml \
  people.xsd

python $1sub.py people.xml 2> $1_warnings.txt | tee $1.xml
