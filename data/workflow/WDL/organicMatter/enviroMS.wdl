workflow fticrmsNOM {

    Array[File] file_paths

    String output_directory

    String output_type

    File corems_json_path

    String polarity

    Int raw_file_start_scan

    Int raw_file_final_scan

    Boolean is_centroid

    File calibration_ref_file_path

    Boolean calibrate

    Boolean plot_mz_error

    Boolean plot_ms_assigned_unassigned

    Boolean plot_c_dbe

    Boolean plot_van_krevelen

    Boolean plot_ms_classes

    Boolean plot_mz_error_classes

    Int jobs_count = 1

   call runDirectInfusion {
	input:
		output_directory = output_directory,
		file_paths = file_paths,
		output_type=output_type,
		corems_json_path=corems_json_path,
		polarity=polarity,
		raw_file_start_scan=raw_file_start_scan,
		raw_file_final_scan=raw_file_final_scan,
		is_centroid=is_centroid,
		calibration_ref_file_path=calibration_ref_file_path,
		calibrate=calibrate,
		plot_mz_error_classes=plot_mz_error_classes,
		plot_mz_error=plot_mz_error,
		plot_ms_assigned_unassigned=plot_ms_assigned_unassigned,
		plot_c_dbe=plot_c_dbe,
		plot_van_krevelen=plot_van_krevelen,
		plot_ms_classes=plot_ms_classes,
		jobs_count=jobs_count
	}

   call filter_molecules {
        input:
		file_paths = file_paths,
		output_directory = output_directory,
		out = runDirectInfusion.out
		
             }
}

task runDirectInfusion {
    
    Array[File] file_paths

    String output_directory

    String output_type

    File corems_json_path

    String polarity

    Int raw_file_start_scan

    Int raw_file_final_scan

    Boolean is_centroid

    File calibration_ref_file_path

    Boolean calibrate

    Boolean plot_mz_error

    Boolean plot_ms_assigned_unassigned

    Boolean plot_c_dbe

    Boolean plot_van_krevelen

    Boolean plot_ms_classes

    Boolean plot_mz_error_classes
    
    Int jobs_count = 1
    
    command {
 
        enviroMS run-di-wdl ${sep="," file_paths} \
                                     ${output_directory} \
                                     ${output_type} \
                                     ${corems_json_path} \
                                     ${polarity} \
                                     ${raw_file_start_scan} \
                                     ${raw_file_final_scan} \
                                     ${is_centroid} \
                                     ${calibration_ref_file_path} \
                                     -c ${calibrate} \
                                     -e ${plot_mz_error} \
                                     -a ${plot_ms_assigned_unassigned} \
                                     -cb ${plot_c_dbe} \
                                     -vk ${plot_van_krevelen} \
                                     -mc ${plot_ms_classes} \
                                     -ec ${plot_mz_error_classes} \
                                     --jobs ${jobs_count} 
    }
    
    output {
        
        String out = read_string(stdout())
        Array[File] output_files = glob('${output_directory}/**/*.*')
        Array[File] van_krevelen_plots = glob('${output_directory}/**/van_krevelen/*.*')
        Array[File] dbe_vs_c_plots = glob('${output_directory}/**/dbe_vs_c/*.*')
        Array[File] ms_class_plots = glob('${output_directory}/**/ms_class/*.*')
        Array[File] mz_error_class_plots = glob('${output_directory}/**/mz_error_class/*.*')
        
    }   

    runtime {

        docker: "microbiomedata/enviroms:4.2.1"
    
    }

}

task filter_molecules {

    Array[File] file_paths
    String out 
    String dollar="$"
    String output_directory 


    command <<<

	for i in ${sep=',' file_paths}
        do
	   filename=${dollar}(basename $i)
	   proj=${dollar}{filename%.*}
	done

	python <<CODE
	import json
	import pandas as pd   

	#get filnames basename
	molecules_csv = '${output_directory}/$proj/$proj.csv'

	df = pd.read_csv(molecules_csv)
	filtered_df = df.dropna(subset=['Molecular Formula'])
	filtered_df = filtered_df.sort_values('Confidence Score', ascending = False)

        #write out to tsv
	filtered_df.to_csv('enviroms_sorted_molecules.tsv', sep = '\t', index = False)
    
        #filter top 100 for rendering 
	top100 = filtered_df[:100]
	top100.to_json('top100_molecules.json' , orient = 'records', indent=2)

	CODE

	cp enviroms_sorted_molecules.tsv top100_molecules.json ${output_directory}/$proj/

   >>>


   output {

	File filtered_csv = "enviroms_sorted_molecules.tsv"
	File top100 = "top100_molecules.json"
    }

    runtime {

        docker: "microbiomedata/enviroms:4.2.1"

    }

}
