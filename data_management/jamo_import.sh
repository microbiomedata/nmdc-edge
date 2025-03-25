#!/bin/bash

# run this script from /jamo_metadata

declare -A wf_dict=(
  ["wfmag"]="nmdc_mags_analysis"
  ["wfmgan"]="nmdc_metagenome_annotation"
  ["wfmgas"]="nmdc_metagenome_assembly"
  ["wfrbt"]="nmdc_read_based_taxonomy_analysis"
  ["wfrqc"]="nmdc_readqc_analysis"
)

cd metadata_files
module load jamo

for file in metadata*.json; do
  wf=$(echo "$file" | cut -d':' -f3 | cut -d'-' -f1)
  jat import ${wf_dict[$wf]} $file
  mv $file ${file}.done
done
