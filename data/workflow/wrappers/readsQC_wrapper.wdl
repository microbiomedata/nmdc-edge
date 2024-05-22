import "rqcfilter.wdl" as ReadsQC
import "readsqc_output.wdl" as ReadsQC_output
import "readsqc_preprocess.wdl" as readsqc_preprocess

workflow main_workflow {
    Array[File] input_files
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.92"
    String database="/refdata"
    String memory="60g"
    String threads="4"
    Boolean input_interleaved=true
    Array[File] input_fq1
    Array[File] input_fq2
    String? prefix

    call readsqc_preprocess.readsqc_preprocess as readsqc_preprocess {
        input:
            input_files=input_files,
            outdir=outdir,
            input_interleaved=input_interleaved,
            input_fq1=input_fq1,
            input_fq2=input_fq2
    }

    scatter (file in select_first([readsqc_preprocess.input_files_gz, [""]])) {

            call ReadsQC.nmdc_rqcfilter  as nmdc_rqcfilter {
                input:
                    input_files=file,
                    database=database,
                    proj=prefix
        }

    }

    call ReadsQC_output.readsqc_output as readsqc_output {
        input:
            input_files = nmdc_rqcfilter.filtered_final,
            filtered_stats_final = nmdc_rqcfilter.filtered_stats_final,
            filtered_stats2_final = nmdc_rqcfilter.filtered_stats2_final,
            rqc_info = nmdc_rqcfilter.rqc_info,
            filtered_stats_json_final = nmdc_rqcfilter.filtered_stats_json_final,
            outdir = outdir
    }
}
