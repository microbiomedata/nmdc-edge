import "viral-plasmid_tasks.wdl" as tasks

workflow viral {
        String database
        String genomad_db = database + '/genomad_db-v1.3'
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
        String docker = "mbabinski17/genomad:1.5.2"
        String checkV_docker = "mbabinski17/checkv:1.0.1"

    call tasks.geNomad_full as gn {
        input: ASM_FASTA = fasta,
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
        input: VIRUS_FASTA = gn.virus_fasta,
                CHECKV_DB = checkv_db,
                OUTDIR = outdir,
                DOCKER = checkV_docker
        }

}