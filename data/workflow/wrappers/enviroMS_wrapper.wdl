import "enviroMS.wdl" as NOM

workflow main_workflow {
    Array[File] file_paths
    String output_directory
    String output_type
    Boolean calibrate
    File? calibration_ref_file_path
    File corems_json_path
    String polarity
    Boolean is_centroid
    Int raw_file_start_scan
    Int raw_file_final_scan
    Boolean plot_mz_error
    Boolean plot_ms_assigned_unassigned
    Boolean plot_c_dbe
    Boolean plot_van_krevelen
    Boolean plot_ms_classes
    Boolean plot_mz_error_classes

    call NOM.fticrmsNOM as fticrmsNOM {
        input: 
            file_paths=file_paths,
            output_directory=output_directory,
            output_type=output_type,
            calibrate=calibrate,
            calibration_ref_file_path=calibration_ref_file_path,
            corems_json_path=corems_json_path,
            polarity=polarity,
            is_centroid=is_centroid,
            raw_file_start_scan=raw_file_start_scan,
            raw_file_final_scan=raw_file_final_scan,
            plot_mz_error=plot_mz_error,
            plot_ms_assigned_unassigned=plot_ms_assigned_unassigned,
            plot_c_dbe=plot_c_dbe,
            plot_van_krevelen=plot_van_krevelen,
            plot_ms_classes=plot_ms_classes,
            plot_mz_error_classes=plot_mz_error_classes
    }
}
