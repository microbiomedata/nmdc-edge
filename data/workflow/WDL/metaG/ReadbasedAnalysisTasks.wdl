task profilerGottcha2 {
    Array[File] READS
    String DB
    String PREFIX
    String? RELABD_COL = "ROLLUP_DOC"
    String DOCKER
    Int? CPU = 4

    command <<<
        set -euo pipefail

        gottcha2.py -r ${RELABD_COL} \
                    -i ${sep=' ' READS} \
                    -t ${CPU} \
                    -o . \
                    -p ${PREFIX} \
                    --database ${DB}
        
        grep "^species" ${PREFIX}.tsv | ktImportTaxonomy -t 3 -m 9 -o ${PREFIX}.krona.html - || true
    >>>
    output {
        File report_tsv = "${PREFIX}.tsv"
        File full_tsv = "${PREFIX}.full.tsv"
        File krona_html = "${PREFIX}.krona.html"
    }
    runtime {
        docker: DOCKER
	database: DB
        cpu: CPU
        node: 1
        nwpn: 1
        memory: "45G"
        time: "04:00:00"
    }
    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
    }
}

task profilerCentrifuge {
    Array[File] READS
    String DB
    String PREFIX
    Int? CPU = 4
    String DOCKER

    command <<<
        set -euo pipefail
        eval "$(/opt/conda/bin/conda shell.bash hook)"
        conda activate centrifuge
        centrifuge -x ${DB} \
                   -p ${CPU} \
                   -U ${sep=',' READS} \
                   -S ${PREFIX}.classification.tsv \
                   --report-file ${PREFIX}.report.tsv
        conda deactivate

        ktImportTaxonomy -m 5 -t 2 -o ${PREFIX}.krona.html ${PREFIX}.report.tsv
    >>>
    output {
      File classification_tsv="${PREFIX}.classification.tsv"
      File report_tsv="${PREFIX}.report.tsv"
      File krona_html="${PREFIX}.krona.html"
    }
    runtime {
        docker: DOCKER
	database: DB
        cpu: CPU
        node: 1
        nwpn: 1
        memory: "45G"
        time: "04:00:00"
    }
    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
    }
}

task profilerKraken2 {
    Array[File] READS
    String DB
    String PREFIX
    Boolean? PAIRED = false
    Int? CPU = 4
    String DOCKER

    command <<<
        set -euo pipefail
        eval "$(/opt/conda/bin/conda shell.bash hook)"
        conda activate kraken
        kraken2 ${true="--paired" false='' PAIRED} \
                --threads ${CPU} \
                --db ${DB} \
                --output ${PREFIX}.classification.tsv \
                --report ${PREFIX}.report.tsv \
                ${sep=' ' READS}
        conda deactivate

        ktImportTaxonomy -m 3 -t 5 -o ${PREFIX}.krona.html ${PREFIX}.report.tsv
    >>>
    output {

      File classification_tsv = "${PREFIX}.classification.tsv"
      File report_tsv = "${PREFIX}.report.tsv"
      File krona_html = "${PREFIX}.krona.html"
    }
    runtime {
        docker: DOCKER
	database: DB
        cpu: CPU
        node: 1
        nwpn: 1
        memory: "45G"
        time: "04:00:00"
    }
    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
    }
}

task generateSummaryJson {
    File? gottcha2_report_tsv
    File? gottcha2_full_tsv
    File? gottcha2_krona_html
    File? centrifuge_classification_tsv
    File? centrifuge_report_tsv
    File? centrifuge_krona_html
    File? kraken2_classification_tsv
    File? kraken2_report_tsv
    File? kraken2_krona_html
    Map[String, String] gottcha_results = {
            "tool": "gottcha2",
            "orig_out_tsv": "${gottcha2_full_tsv}",
            "orig_rep_tsv": "${gottcha2_report_tsv}",
            "krona_html": "${gottcha2_krona_html}"
    }
    Map[String, String] centrifuge_results = {
            "tool": "centrifuge",
            "orig_out_tsv": "${centrifuge_classification_tsv}",
            "orig_rep_tsv": "${centrifuge_report_tsv}",
            "krona_html": "${centrifuge_krona_html}"
    }
    Map[String, String] kraken2_results = {
            "tool": "kraken2",
            "orig_out_tsv": "${kraken2_classification_tsv}",
            "orig_rep_tsv": "${kraken2_report_tsv}",
            "krona_html": "${kraken2_krona_html}"
    }
    Array[Map[String, String]?] TSV_META_JSON = [gottcha_results,centrifuge_results,kraken2_results]
    String PREFIX
    String OUT = PREFIX + ".json"
    String DOCKER

    command {
        outputTsv2json.py --meta ${write_json(TSV_META_JSON)} > ${OUT}
    }
    output {
        File summary_json = "${OUT}"
    }
    runtime {
        docker: DOCKER
        node: 1
        nwpn: 1
        memory: "45G"
        time: "04:00:00"
    }
    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
    }
}
