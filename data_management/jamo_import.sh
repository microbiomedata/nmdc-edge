#!/bin/bash

# run this script from /metadata_files

declare -A wf_dict=(
  ["wfmag"]="nmdc_mags_analysis.yaml"
  ["wfmgan"]="nmdc_metagenome_annotation.yaml"
  ["wfmgas"]="nmdc_metagenome_assembly.yaml"
  ["wfrbt"]="nmdc_read_based_taxonomy_analysis.yaml"
  ["wfrqc"]="nmdc_readqc_analysis.yaml"
)

module load jamo/dev

for file in metadata*.json; do
  wf=$(echo "$file" | cut -d':' -f3 | cut -d'-' -f1)
#  echo  $wf, ${wf_dict[$wf]}
  jat import nmdc-shal-test/${wf_dict[$wf]} $file
  mv $file ${file}.done
done
