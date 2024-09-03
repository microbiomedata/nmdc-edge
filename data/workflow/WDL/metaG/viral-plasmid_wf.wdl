version 1.0

import "viral-plasmid_tasks.wdl" as tasks

workflow viral {
    input {
        String database
        String genomad_db = database + '/genomad_db-v1.6'
        String checkv_db = database + '/checkv-db-v1.4'
        File fasta
        Map[String, Boolean] option
        Float? min_score
        Int? min_virus_hallmark
        Int? min_plasmid_hallmark
        Int? min_plasmid_hallmarks_short_seqs
        Int? min_virus_hallmarks_short_seqs
        Float? min_plasmid_marker_enrichment
        Float? min_virus_marker_enrichment
        Int? max_uscg
        Boolean? score_calibration
        Float? fdr
        Int cpu
        String outdir
        String docker = "mbabinski17/genomad:1.7.1"
        String checkV_docker = "mbabinski17/checkv:1.0.1"
        }

    call tasks.geNomad_full as gn {
        input: 
            ASM_FASTA = fasta,
            GENOMAD_DB = genomad_db,
            OPTION = option,
            min_score = min_score,
            min_virus_hallmark = min_virus_hallmark,
            min_plasmid_hallmark = min_plasmid_hallmark,
            min_plasmid_hallmarks_short_seqs = min_plasmid_hallmarks_short_seqs,
            min_virus_hallmarks_short_seqs = min_virus_hallmarks_short_seqs,
            min_plasmid_marker_enrichment = min_plasmid_marker_enrichment,
            min_virus_marker_enrichment = min_virus_marker_enrichment,
            max_uscg = max_uscg,
            calibration = score_calibration,
            fdr=fdr,
            OUTDIR = outdir,
            CPU = cpu,
            DOCKER = docker
        }

    call tasks.checkV {
        input: 
            VIRUS_FASTA = gn.virus_fasta,
            CHECKV_DB = checkv_db,
            OUTDIR = outdir,
            DOCKER = checkV_docker
        }
    output {
        #geNomad_full
        File plasmids_fasta = gn.plasmids_fasta 
        File plasmid_genes = gn.plasmid_genes 
        File plasmid_protiens = gn.plasmid_protiens
        File plasmid_summary = gn.plasmid_summary
        File virus_fasta = gn.virus_fasta
        File virus_genes = gn.virus_genes 
        File virus_proteins = gn.virus_proteins
        File virus_summary = gn.virus_summary
        File summary_log = gn.summary_log
        File aggregated_log = gn.aggregated_log
        File annotate_log = gn.annotate_log
        File provirus_log = gn.provirus_log    
        File marker_log = gn.marker_log
        File nn_log = gn.nn_log
        #CheckV
        File quality_summary = checkV.quality_summary
        File completeness_tsv = checkV.completeness_tsv 
        File contamination_tsv = checkV.contamination_tsv 
        File complete_genomes = checkV.complete_genomes
    }
}