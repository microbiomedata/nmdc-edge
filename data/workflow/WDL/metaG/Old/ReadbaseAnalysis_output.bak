version 1.0

workflow ReadbasedAnalysis_output {
    input {
        Array[File] reads
        Int cpu
        String prefix
        String outdir
        File gottcha2_report_tsv
        File gottcha2_full_tsv
        File gottcha2_krona_html
        File centrifuge_classification_tsv
        File centrifuge_report_tsv
        File centrifuge_krona_html
        File kraken2_classification_tsv
        File kraken2_report_tsv
        File kraken2_krona_html
        File summary_json
        String? docker = "microbiomedata/nmdc_taxa_profilers:1.0.3p1"
    }

    call make_outputs {
        input: gottcha2_report_tsv = gottcha2_report_tsv,
               gottcha2_full_tsv = gottcha2_full_tsv,
               gottcha2_krona_html = gottcha2_krona_html,
               centrifuge_classification_tsv = centrifuge_classification_tsv,
               centrifuge_report_tsv = centrifuge_report_tsv,
               centrifuge_krona_html = centrifuge_krona_html,
               kraken2_classification_tsv = kraken2_classification_tsv,
               kraken2_report_tsv = kraken2_report_tsv,
               kraken2_krona_html = kraken2_krona_html,
               summary_json = summary_json,
               outdir = outdir,
               PREFIX = prefix,
               container = docker
    }
}

task make_outputs{
    input {
        String outdir
        File? gottcha2_report_tsv
        File? gottcha2_full_tsv
        File? gottcha2_krona_html
        File? centrifuge_classification_tsv
        File? centrifuge_report_tsv
        File? centrifuge_krona_html
        File? kraken2_classification_tsv
        File? kraken2_report_tsv
        File? kraken2_krona_html
        File? summary_json
        String PREFIX
        String? container
    }

    command<<<
        set -euo pipefail
        mkdir -p ${outdir}/gottcha2
        cp ${gottcha2_report_tsv} ${gottcha2_full_tsv} ${gottcha2_krona_html} \
           ${outdir}/gottcha2
        mkdir -p ${outdir}/centrifuge
        cp ${centrifuge_classification_tsv} ${centrifuge_report_tsv} ${centrifuge_krona_html} \
           ${outdir}/centrifuge
        mkdir -p ${outdir}/kraken2
        cp ${kraken2_classification_tsv} ${kraken2_report_tsv} ${kraken2_krona_html} \
           ${outdir}/kraken2
        cp ${summary_json} ${outdir}/
    >>>
    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
    output{
        File? summary = "${outdir}/${PREFIX}.json"
    }
}