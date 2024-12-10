version 1.0

workflow readbasedAnalysis_output {
    input {
        String? outdir
        File gottcha2_report_tsv
        File gottcha2_full_tsv
        File gottcha2_krona_html
        File centrifuge_report_tsv
        File centrifuge_classification_tsv
        File centrifuge_krona_html
        File kraken2_report_tsv
        File kraken2_classification_tsv
        File kraken2_krona_html
        Map[String, String] gottcha_result = {
            "tool": "gottcha2",
            "orig_out_tsv": "~{gottcha2_full_tsv}",
            "orig_rep_tsv": "~{gottcha2_report_tsv}",
            "krona_html": "~{gottcha2_krona_html}"
        }   
        Map[String, String] centrifuge_result = {
            "tool": "centrifuge",
            "orig_out_tsv": "~{centrifuge_classification_tsv}",
            "orig_rep_tsv": "~{centrifuge_report_tsv}",
            "krona_html": "~{centrifuge_krona_html}"
        }
        Map[String, String] kraken2_result = {
            "tool": "kraken2",
            "orig_out_tsv": "~{kraken2_classification_tsv}",
            "orig_rep_tsv": "~{kraken2_report_tsv}",
            "krona_html": "~{kraken2_krona_html}"
        }
        Array[Map[String, String]?] TSV_META_JSON = [gottcha_result, centrifuge_result, kraken2_result]
        String docker = "poeli/nmdc_taxa_profilers:1.0.3p2"
        String bbtools_container="microbiomedata/bbtools:38.96"
        String PREFIX
    }

    call generateSummaryJson {
        input: 
            PREFIX = PREFIX,
            DOCKER = docker,
            TSV_META_JSON=TSV_META_JSON
    }

    call make_output{
        input:
            outdir=outdir,
            gottcha2_report_tsv=gottcha2_report_tsv, 
            gottcha2_full_tsv=gottcha2_full_tsv,
            gottcha2_krona_html=gottcha2_krona_html, 
            kraken2_report_tsv=kraken2_report_tsv,
            kraken2_classification_tsv=kraken2_classification_tsv, 
            kraken2_krona_html=kraken2_krona_html,
            centrifuge_report_tsv=centrifuge_report_tsv,
            centrifuge_classification_tsv=centrifuge_classification_tsv,
            centrifuge_krona_html=centrifuge_krona_html,
            summary_json=generateSummaryJson.summary_json,
            container=bbtools_container
    }
    
    output {
            File summary_json=generateSummaryJson.summary_json
    }

}

task generateSummaryJson {
    input {
        String PREFIX
        String OUT = PREFIX + ".json"
        String DOCKER
        Array[Map[String, String]?] TSV_META_JSON
    }
    command <<<
    
        set -euo pipefail
        outputTsv2json.py --meta ~{write_json(TSV_META_JSON)} > ~{OUT}
        
    >>>
    output {
        File summary_json = "~{OUT}"
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

task make_output{
    input{
        String? outdir
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
        String container
    }

    command <<<

        set -euo pipefail
        mkdir -p ~{outdir}

        cp ~{summary_json} ~{outdir}/

        mkdir -p ~{outdir}/gottcha2/
        mkdir -p ~{outdir}/centrifuge/
        mkdir -p ~{outdir}/kraken2/

        cp ~{gottcha2_report_tsv} ~{gottcha2_full_tsv} ~{gottcha2_krona_html} ~{outdir}/gottcha2/
        cp ~{centrifuge_classification_tsv} ~{centrifuge_report_tsv} ~{centrifuge_krona_html} ~{outdir}/centrifuge/
        cp ~{kraken2_classification_tsv} ~{kraken2_report_tsv} ~{kraken2_krona_html} ~{outdir}/kraken2/

    >>>

    runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
    }

}