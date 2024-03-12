import "ReadbasedAnalysisTasks.wdl" as tasks

workflow ReadbasedAnalysis {
    Map[String, Boolean] enabled_tools
    String db_gottcha2 = "/refdata/GOTTCHA2_fungal/gottcha_db.BAVFPt.species.fna"
    String db_kraken2 = "/refdata/Kraken2/"
    String db_centrifuge = "/refdata/Centrifuge/hpv"
    Array[File] reads
    Int cpu
    String prefix
    String outdir
    Boolean? paired = false
    String? docker = "poeli/nmdc_taxa_profilers:1.0.6"

    if (enabled_tools["gottcha2"] == true) {
        call tasks.profilerGottcha2 {
            input: READS = reads,
                   DB = db_gottcha2,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }

    if (enabled_tools["kraken2"] == true) {
        call tasks.profilerKraken2 {
            input: READS = reads,
                   PAIRED = paired,
                   DB = db_kraken2,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }

    if (enabled_tools["centrifuge"] == true) {
        call tasks.profilerCentrifuge {
            input: READS = reads,
                   DB = db_centrifuge,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }
    
	call tasks.generateSummaryJson {
        input: gottcha2_report_tsv = profilerGottcha2.report_tsv,
               gottcha2_full_tsv = profilerGottcha2.full_tsv,
               gottcha2_krona_html = profilerGottcha2.krona_html,
               centrifuge_classification_tsv = profilerCentrifuge.classification_tsv,
               centrifuge_report_tsv = profilerCentrifuge.report_tsv,
               centrifuge_krona_html = profilerCentrifuge.krona_html,
               kraken2_classification_tsv = profilerKraken2.classification_tsv,
               kraken2_report_tsv = profilerKraken2.report_tsv,
               kraken2_krona_html = profilerKraken2.krona_html,
               PREFIX = prefix,
               DOCKER = docker
    }
    
    call make_outputs {
        input: gottcha2_report_tsv = profilerGottcha2.report_tsv,
               gottcha2_full_tsv = profilerGottcha2.full_tsv,
               gottcha2_krona_html = profilerGottcha2.krona_html,
               centrifuge_classification_tsv = profilerCentrifuge.classification_tsv,
               centrifuge_report_tsv = profilerCentrifuge.report_tsv,
               centrifuge_krona_html = profilerCentrifuge.krona_html,
               kraken2_classification_tsv = profilerKraken2.classification_tsv,
               kraken2_report_tsv = profilerKraken2.report_tsv,
               kraken2_krona_html = profilerKraken2.krona_html,
               summary_json = generateSummaryJson.summary_json,
               outdir = outdir,
               PREFIX = prefix,
               container = docker
    }

    

    output {
        File? gottcha2_report_tsv = profilerGottcha2.report_tsv
        File? gottcha2_full_tsv = profilerGottcha2.full_tsv
        File? gottcha2_krona_html = profilerGottcha2.krona_html
        File? centrifuge_classification_tsv = profilerCentrifuge.classification_tsv
        File? centrifuge_report_tsv = profilerCentrifuge.report_tsv
        File? centrifuge_krona_html = profilerCentrifuge.krona_html
        File? kraken2_classification_tsv = profilerKraken2.classification_tsv
        File? kraken2_report_tsv = profilerKraken2.report_tsv
        File? kraken2_krona_html = profilerKraken2.krona_html
        File? summary_json = generateSummaryJson.summary_json
    }

    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
        version: "1.0.2"
    }
}


task make_outputs{
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
    String container

    command<<<
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

