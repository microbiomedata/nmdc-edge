#!/bin/bash

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
