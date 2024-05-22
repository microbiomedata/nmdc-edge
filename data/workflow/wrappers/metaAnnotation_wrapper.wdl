import "annotation_full.wdl" as MetaAnnotation
import "annotation_output.wdl" as MetaAnnotationOutput

workflow main_workflow {
    String  input_file
    String  imgap_project_id
    String  outdir
    Int     additional_threads=42
    String  database_location="/refdata/img/"

    call MetaAnnotation.annotation as annotation {
        input: 
            input_file=input_file, 
            proj=imgap_project_id,
            imgap_project_id=imgap_project_id, 
            additional_threads=additional_threads, 
            database_location=database_location
    }
    call MetaAnnotationOutput.annotation_output as annotation_output {
        input:
            imgap_project_type=imgap_project_id, 
            outdir=outdir, 
            final_stats_tsv=annotation.stats_tsv, 
            functional_gff=annotation.functional_gff
    }
}

