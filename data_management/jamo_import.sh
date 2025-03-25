#!/bin/bash
# Usage: jamo_import.sh <path_to_metadata_dir>

# Example:
# cd /global/cfs/cdirs/m3408/jamo_metadata ;
# jamo_import.sh /global/cfs/cdirs/m3408/jamo_metadata/metadata_files 2>&1 | tee jamo_import.log

declare -A wf_dict=(
  ["wfmag"]="nmdc_mags_analysis"
  ["wfmgan"]="nmdc_metagenome_annotation"
  ["wfmgas"]="nmdc_metagenome_assembly"
  ["wfrbt"]="nmdc_read_based_taxonomy_analysis"
  ["wfrqc"]="nmdc_readqc_analysis"
)

cd $1
module load jamo

# todo check for workflow_execution record in jamo

for file in metadata*.json; do
  wf=$(echo "$file" | cut -d':' -f3 | cut -d'-' -f1)
  jat import ${wf_dict[$wf]} $file
  mv $file ${file}.done
  echo "Imported $file"
done
