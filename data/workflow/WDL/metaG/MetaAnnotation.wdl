import "annotation_full.wdl" as MetaAnnotation
import "annotation_output.wdl" as MetaAnnotationOutput

workflow main_workflow {
    String  MetaAnnotation_input_file
    String  MetaAnnotation_imgap_project_id
    String  MetaAnnotation_outdir
    Int     MetaAnnotation_additional_threads=42
    String  MetaAnnotation_database_location="/refdata/img/"

    call MetaAnnotation.annotation as annotation {
        input: input_file=MetaAnnotation_input_file, proj=MetaAnnotation_imgap_project_id,imgap_project_id=MetaAnnotation_imgap_project_id, additional_threads=MetaAnnotation_additional_threads, database_location=MetaAnnotation_database_location
    }
    call MetaAnnotationOutput.annotation_output as annotation_output {
        input:imgap_project_type=MetaAnnotation_imgap_project_id, outdir=MetaAnnotation_outdir, final_stats_tsv=annotation.stats_tsv, functional_gff=annotation.functional_gff
    }
}
