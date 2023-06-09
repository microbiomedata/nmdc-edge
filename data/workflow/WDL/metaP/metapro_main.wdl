version 1.0

import "run_job_analysis.wdl" as run_analysis
import "report_gen.wdl" as generate_reports
import "metadata_coll.wdl" as collect_metadata

workflow metapro {
    Int fasta_split_on_size_mb = 1000
    Int fasta_split_count = 22
    String pipeline_type = "nmdc:MetaProteomicAnalysis"
    String git_url = "https://github.com/microbiomedata/metaPro/releases/tag/2.0.0"

    input{
        Array[Object] mapper_list
        String QVALUE_THRESHOLD
        File MASIC_PARAM_FILE_LOC
        File MSGFPLUS_PARAM_FILE_LOC
        File CONTAMINANT_FILE_LOC
        String STUDY
        String EXECUTION_RESOURCE
        String DATA_URL
        String OUTDIR
    }

    scatter (myobj in mapper_list) {
        call run_analysis.job_analysis {
            input:
                dataset_name            = basename(myobj['raw_file_loc'], ".raw"),
                annotation_name         = basename(myobj['faa_file_loc'], "_proteins.faa"),
                raw_file_loc            = myobj['raw_file_loc'],
                faa_file_loc            = myobj['faa_file_loc'],
                thermo                  = myobj['thermo_raw'],
                QVALUE_THRESHOLD        = QVALUE_THRESHOLD,
                MASIC_PARAM_FILENAME    = MASIC_PARAM_FILE_LOC,
                MSGFPLUS_PARAM_FILENAME = MSGFPLUS_PARAM_FILE_LOC,
                CONTAMINANT_FILENAME    = CONTAMINANT_FILE_LOC,
                FASTA_SPLIT_ON_SIZE_MB  = fasta_split_on_size_mb,
                FASTA_SPLIT_COUNT       = fasta_split_count
        }
        call generate_reports.report_gen {
            input:
                faa_txt_file      = job_analysis.faa_with_contaminates,
                gff_file          = myobj['gff_file_loc'],
                resultant_file    = job_analysis.resultant_file,
                Dataset_id        = STUDY,
                genome_directory  = "metapro",
                q_value_threshold = QVALUE_THRESHOLD,
                annotation_name   = basename(myobj['faa_file_loc'],"_proteins.faa"),
                dataset_name      = basename(myobj['raw_file_loc'], ".raw"),
                first_hits_file   = job_analysis.first_hits_file
        }

        Result result = {
            "resultant_file": job_analysis.resultant_file,
            "peptide_report_file": report_gen.peptide_file,
            "protein_report_file": report_gen.protein_file,
            "qc_metric_report_file": report_gen.qc_metric_file,
            "faa_file": myobj['faa_file_loc'],
            "contaminate_file": CONTAMINANT_FILE_LOC,
            "txt_faa_file": report_gen.txt_faa_file,
            "genome_directory": "metapro",
            "dataset_id": STUDY,
            "start_time": job_analysis.start_time,
            "end_time": job_analysis.end_time
        }
    }

    call make_output {
        input:
            outdir = OUTDIR,
            results_file = job_analysis.resultant_file,
            peptide_file = report_gen.peptide_file,
            protein_file = report_gen.protein_file,
            qc_metric_file = report_gen.qc_metric_file,
            txt_faa_file = report_gen.txt_faa_file
    }

    Array[Result?] results_maybe = result
    Array[Result] results = select_all(results_maybe)

    call collect_metadata.gen_metadata {
        input:
            study       = STUDY,
            results     = results,
            pipeline_type = pipeline_type,
            execution_resource = EXECUTION_RESOURCE,
            git_url = git_url,
            data_url = DATA_URL
    }
}

task make_output {
    input{
        String outdir
        Array[File] results_file
        Array[File] peptide_file
        Array[File] protein_file
        Array[File] qc_metric_file
        Array[File] txt_faa_file
    }
    
    command <<<
        mkdir -p ~{outdir}
        cp ~{sep=' ' results_file} ~{outdir}
        cp ~{sep=' ' peptide_file} ~{outdir}
        cp ~{sep=' ' protein_file} ~{outdir}
        cp ~{sep=' ' qc_metric_file} ~{outdir}
        cp ~{sep=' ' txt_faa_file} ~{outdir}
    >>>

    runtime {
        docker: 'microbiomedata/metapro-post-processing:1.1.0'
    }
}