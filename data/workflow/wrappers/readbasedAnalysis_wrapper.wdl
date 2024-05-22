import "ReadbasedAnalysis.wdl" as ReadbasedAnalysis
import "readbasedanalysis_preprocess.wdl" as readbasedanalysis_preprocess
import "readbasedAnalysis_output.wdl" as readbasedAnalysis_output

workflow main_workflow {

    Array[File] reads
    Int cpu = 4
    String prefix
    String outdir
    Boolean? paired = false

    String db_gottcha2 = "/refdata/GOTTCHA2/RefSeq-r90.cg.BacteriaArchaeaViruses.species.fna"
    String db_kraken2 = "/refdata/Kraken2"
    String db_centrifuge = "/refdata/Centrifuge/hpv"

    call readbasedanalysis_preprocess.preprocess as preprocess {
        input:
            input_files=reads,
            paired=paired
    }
    call <WORKFLOW>.ReadbasedAnalysis as ReadbasedAnalysis {
        input: 
            input_file=preprocess.input_file_gz, 
            cpu=cpu,
            proj=prefix,
            paired=paired,
            db_gottcha2=db_gottcha2, 
            db_kraken2=db_kraken2, 
            db_centrifuge=db_centrifuge
    }

    call readbasedAnalysis_output.readbasedAnalysis_output as readbasedAnalysis_output {
        input: 
            gottcha2_report_tsv=ReadbasedAnalysis.final_gottcha2_report_tsv, 
            gottcha2_full_tsv=ReadbasedAnalysis.final_gottcha2_full_tsv,
            gottcha2_krona_html=ReadbasedAnalysis.final_gottcha2_krona_html, 
            kraken2_report_tsv=ReadbasedAnalysis.final_kraken2_report_tsv,
            kraken2_classification_tsv=ReadbasedAnalysis.final_kraken2_classification_tsv, 
            kraken2_krona_html=ReadbasedAnalysis.final_kraken2_krona_html,
            centrifuge_report_tsv=ReadbasedAnalysis.final_centrifuge_report_tsv,
            centrifuge_classification_tsv=ReadbasedAnalysis.final_centrifuge_classification_tsv,
            centrifuge_krona_html=ReadbasedAnalysis.final_centrifuge_krona_html, PREFIX=ReadbasedAnalysis_prefix
    }
}