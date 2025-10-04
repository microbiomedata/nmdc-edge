version 1.0

task geNomad_full {
    input {
        File ASM_FASTA
        String proj_name
        String GENOMAD_DB
        String OUTDIR
        String DOCKER
        Map[String, Boolean] OPTION
        String GeNomad_Summary = OUTDIR + '/geNomad_summary'
        Float? min_score = 0
        Int? min_virus_hallmark = 0
        Int? min_plasmid_hallmark = 0
        Int? min_plasmid_hallmarks_short_seqs = 1
        Int? min_virus_hallmarks_short_seqs = 1
        Float? min_plasmid_marker_enrichment = 0
        Float? min_virus_marker_enrichment = 0
        Int? max_uscg = 4
        Int? CPU = 4
        Boolean? calibration = false
        Float? fdr = 0.1
        String prefix=sub(sub(sub(sub(sub(sub(basename(ASM_FASTA), "\\.fna\\.gz", ""), "\\.fasta\\.gz", ""), "\\.fa\\.gz", ""), "\\.fna", ""), "\\.fasta", ""), "\\.fa", "")
    }

    command <<<

        set -eo pipefail
        cp  ~{ASM_FASTA} ~{proj_name}
        mkdir -p ~{OUTDIR}
        if [ ~{OPTION["default"]} == true ]; then 
            genomad end-to-end --cleanup --splits 4 ~{proj_name} ~{OUTDIR} ~{GENOMAD_DB} \

        fi
        if [ ~{OPTION["relaxed"]} == true ]; then
            genomad end-to-end --relaxed --splits 4 ~{proj_name} ~{OUTDIR} ~{GENOMAD_DB} \

        fi
        if [ ~{OPTION["conservative"]} == true ]; then
            genomad end-to-end --conservative --splits 4 ~{proj_name} ~{OUTDIR} ~{GENOMAD_DB} \
 
        fi
 
        if [ ~{OPTION["custom"]} == true ]; then
            if [ ~{calibration} == true ]; then
                genomad end-to-end --cleanup --splits 4 --min-score ~{min_score} \
                --min-virus-hallmarks ~{min_virus_hallmark} \
                --min-plasmid-hallmarks ~{min_plasmid_hallmark} \
                --min-plasmid-hallmarks-short-seqs ~{min_plasmid_hallmarks_short_seqs} \
                --min-virus-hallmarks-short-seqs ~{min_virus_hallmarks_short_seqs} \
                --min-plasmid-marker-enrichment ~{min_plasmid_marker_enrichment} \
                --min-virus-marker-enrichment ~{min_virus_marker_enrichment} \
                --max-uscg ~{max_uscg} \
                --enable-score-calibration --max-fdr ~{fdr} \
                ~{proj_name} ~{OUTDIR} ~{GENOMAD_DB}
            else
                genomad end-to-end --cleanup --splits 4 --min-score ~{min_score} \
                --min-virus-hallmarks ~{min_virus_hallmark} \
                --min-plasmid-hallmarks ~{min_plasmid_hallmark} \
                --min-plasmid-hallmarks-short-seqs ~{min_plasmid_hallmarks_short_seqs} \
                --min-virus-hallmarks-short-seqs ~{min_virus_hallmarks_short_seqs} \
                --min-plasmid-marker-enrichment ~{min_plasmid_marker_enrichment} \
                --min-virus-marker-enrichment ~{min_virus_marker_enrichment} \
                --max-uscg ~{max_uscg} \
                ~{proj_name} ~{OUTDIR} ~{GENOMAD_DB} 
            fi
        fi
        
        mv OUTDIR/~{proj_name}_summary ~{GeNomad_Summary}
    >>>

    output {
    File plasmids_fasta = "~{GeNomad_Summary}/~{proj_name}_plasmid.fna"
    File plasmid_genes = "~{GeNomad_Summary}/~{proj_name}_plasmid_genes.tsv"
    File plasmid_protiens = "~{GeNomad_Summary}/~{proj_name}_plasmid_proteins.faa"
    File plasmid_summary = "~{GeNomad_Summary}/~{proj_name}_plasmid_summary.tsv"
    File virus_fasta = "~{GeNomad_Summary}/~{proj_name}_virus.fna"
    File virus_genes = "~{GeNomad_Summary}/~{proj_name}_virus_genes.tsv"
    File virus_proteins = "~{GeNomad_Summary}/~{proj_name}_virus_proteins.faa"
    File virus_summary = "~{GeNomad_Summary}/~{proj_name}_virus_summary.tsv"
    File summary_log = "~{OUTDIR}/~{proj_name}_summary.log"
    File aggregated_log = "~{OUTDIR}/~{proj_name}_aggregated_classification.log" 
    File annotate_log = "~{OUTDIR}/~{proj_name}_annotate.log"
    File provirus_log = "~{OUTDIR}/~{proj_name}_find_proviruses.log"
    File marker_log = "~{OUTDIR}/~{proj_name}_marker_classification.log"
    File nn_log = "~{OUTDIR}/~{proj_name}_nn_classification.log"
    }
    runtime {
        docker: DOCKER
        cpu: 8
        node: 1
        memory: "128G"
        time: "06:00:00"
    }
    meta {
        author: "Antonio Camargo, LBNL"
        email: "acamargo@lbnl.gov"
    }
}

task checkV {
    input {
        File VIRUS_FASTA
        String CHECKV_DB
        String? OUTDIR
        # String OUTDIR_v = OUTDIR + '/checkv'
        # String OUTDIR_tmp = OUTDIR_v + '/tmp'
        String DOCKER
        Int CPU = 16
    }

    String OUTDIR_resolved = select_first([OUTDIR, ""])  # Use select_first to default to an empty string if OUTDIR is not provided
    String OUTDIR_v = OUTDIR_resolved + "/checkv"  # Append '/checkv' to OUTDIR
    String OUTDIR_tmp = OUTDIR_v + "/tmp"  # Append '/tmp' to OUTDIR_v

    command <<<

        if [[ ! -s ~{VIRUS_FASTA} ]]; then
            mkdir -p ~{OUTDIR_v}
            echo "none found" > "~{OUTDIR_v}/quality_summary.tsv"
            echo "none found" > "~{OUTDIR_v}/completeness.tsv"
            echo "none found" > "~{OUTDIR_v}/contamination.tsv"
            echo "none found" > "~{OUTDIR_v}/complete_genomes.tsv"
        else
            checkv end_to_end ~{VIRUS_FASTA} ~{OUTDIR_v} -d ~{CHECKV_DB} -t ~{CPU} && \
            rm -rf ~{OUTDIR_tmp}
        fi
    >>>

    output {
        File quality_summary = "~{OUTDIR_v}/quality_summary.tsv"
        File completeness_tsv = "~{OUTDIR_v}/completeness.tsv"
        File contamination_tsv = "~{OUTDIR_v}/contamination.tsv"
        File complete_genomes = "~{OUTDIR_v}/complete_genomes.tsv"
    }

    runtime {
        docker: DOCKER
        cpu: 16
        node: 1
        memory: "64G"
        time: "04:00:00"
    }
    meta {
        author: "Antonio Camargo, LBNL"
        email: "acamargo@lbnl.gov"
    }
}

