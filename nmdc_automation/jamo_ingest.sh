#!/bin/bash

# Find products to ingest
    # connect to mongodb
    # iterate thorugh the records
    # use url suffix to impute nersc based files
    # access the nersc files


# Generate metadata.json
    # generate metadata section
        # workflow_execution - impute from filename
        # workflow_execution_id - curr_dir
        # data_object_id - query api for filename
        # was_informed_by - parent_dir
    # generate outputs section
        # file - filename
        # label - impute from: filename => data_object_id => data_object_type => label from template
        # file_format - impute from filename
        

# Archive into JAMO     
## batch processing?
    # log into perlmutter.nersc.gov
    # module load jamo/dev
    # jat import nmdc-shal-test/nmdc-test-template metadata.json

# Logging


# ##############################################################################################

# DRAFT

# Base directory
base_dir="results"

# First, find all par_dirs in results
for par_dir in "$base_dir"/*/ ; do
    # Then, find all curr_dirs in each par_dir
    for curr_dir in "$par_dir"/*/ ; do
        # Skip if not a directory
        [ ! -d "$curr_dir" ] && continue
        
        # Create metadata.json for each curr_dir
        metadata_file="$curr_dir/metadata.json"
        
        # Start the JSON structure
        echo "{" > "$metadata_file"
        echo '  "workflow_execution": "rqc",' >> "$metadata_file"
        echo '  "outputs": [' >> "$metadata_file"
        
        # Process each file in the current directory
            
            # Add file entry
            echo "    {" >> "$metadata_file"
            echo "      \"filename\": \"$filename\"," >> "$metadata_file"
            echo "      \"label\": \"filtered_final\"" >> "$metadata_file"
            echo -n "    }" >> "$metadata_file"
        done
        
        # Close the JSON structure
        echo >> "$metadata_file"
        echo "  ]" >> "$metadata_file"
        echo "}" >> "$metadata_file"
        
        echo "Generated metadata.json in $curr_dir"
    done
done
