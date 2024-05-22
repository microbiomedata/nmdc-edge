import "viral-plasmid_wf.wdl" as virus_plasmid

workflow main_workflow {
    String database
    File fasta
    Float? min_score
    Int? min_virus_hallmark
    Int? min_plasmid_hallmark
    Int cpu
    Map[String, Boolean] option
    Int? min_plasmid_hallmarks_short_seqs
    Int? min_virus_hallmarks_short_seqs
    Float? min_plasmid_marker_enrichment
    Float? min_virus_marker_enrichment
    Int? max_uscg
    Boolean? score_calibration
    Float? fdr
    String outdir
    
    call virus_plasmid.viral as viral {
        input: 
            database=database,
            fasta=fasta,
            min_score=min_score,
            min_virus_hallmark=min_virus_hallmark,
            min_plasmid_hallmark=min_plasmid_hallmark,
            cpu=cpu,
            option=option,
            min_plasmid_hallmarks_short_seqs=min_plasmid_hallmarks_short_seqs,
            min_virus_hallmarks_short_seqs=min_virus_hallmarks_short_seqs,
            min_plasmid_marker_enrichment=min_plasmid_marker_enrichment,
            min_virus_marker_enrichment=min_virus_marker_enrichment,
            max_uscg=max_uscg,
            score_calibration=score_calibration,
            fdr=fdr,
            outdir=outdir
    }
}