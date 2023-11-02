#!/bin/bash
#

# IMG=microbiomedata/workflowmeta:1.0.5.1
IMG=biocontainers/samtools:1.3.1

if [ "$1" = "inside" ] ; then
	in=$2
	out=$3
	old=$4
	new=$5
	echo "Rewriting $out"
	samtools view -h $in | sed "s/${old}/${new}/g" | \
          samtools view -hb -o $out
else 
	touch $2
	#shifter --image=$IMG $0 inside $@
fi

