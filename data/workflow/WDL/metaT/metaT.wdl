# metaT workflow wrapper
version 1.0

import "https://raw.githubusercontent.com/microbiomedata/metaT/nmdc-import/metaT.wdl" as metaT


workflow nmdc_metat {

    input {
        String  project_id
	    File?   input_file 
        File?   input_fq1
        File?   input_fq2
        Boolean input_interleaved = false
        String  strand_type = " "
        Int     rqc_mem = 190
        Int     rqc_thr = 32
        Int     anno_mem = 200
        Int     anno_thr = 32
    }

    call metaT.nmdc_metat as mt {
        input:
        project_id = project_id,
        input_file = input_file, 
        input_fq1 = input_fq1,
        input_fq2 = input_fq2,
        input_interleaved = input_interleaved,
        strand_type = strand_type,
        rqc_mem = rqc_mem,
        rqc_thr = rqc_thr,
        anno_mem = anno_mem,
        anno_thr = anno_thr
    }

    output { 
        # metaT_ReadsQC
        File filtered_final = mt.filtered_final
        File filtered_stats_final = mt.filtered_stats_final
        File filtered_stats2_final = mt.filtered_stats2_final
        File rqc_info = mt.rqc_info
        File rqc_stats = mt.rqc_stats
        File filtered_ribo_final = mt.filtered_ribo_final
        # metaT_Assembly
        File final_tar_bam = mt.final_tar_bam
        File final_contigs = mt.final_contigs
        File final_scaffolds = mt.final_scaffolds
        File final_asse_log = mt.final_asse_log
        File final_readlen = mt.final_readlen
        File final_sam = mt.final_sam
        File final_bam = mt.final_bam
        File final_bamidx = mt.final_bamidx
        File final_cov = mt.final_cov
        File final_asmstats = mt.final_asmstats
        File asse_info = mt.asse_info
        # mg_annotation
        File proteins_faa = mt.proteins_faa
        File structural_gff = mt.structural_gff
        File ko_ec_gff = mt.ko_ec_gff
        File gene_phylogeny_tsv = mt.gene_phylogeny_tsv
        File functional_gff = mt.functional_gff
        File ko_tsv = mt.ko_tsv
        File ec_tsv = mt.ec_tsv
        File lineage_tsv = mt.lineage_tsv
        File stats_tsv = mt.stats_tsv
        File stats_json = mt.stats_json
        File cog_gff = mt.cog_gff
        File pfam_gff = mt.pfam_gff
        File tigrfam_gff = mt.tigrfam_gff
        File smart_gff = mt.smart_gff
        File supfam_gff = mt.supfam_gff
        File cath_funfam_gff = mt.cath_funfam_gff
        File crt_gff = mt.crt_gff
        File genemark_gff = mt.genemark_gff
        File prodigal_gff = mt.prodigal_gff
        File trna_gff = mt.trna_gff
        File final_rfam_gff = mt.final_rfam_gff
        File product_names_tsv = mt.product_names_tsv
        File crt_crisprs = mt.crt_crisprs
        File imgap_version = mt.imgap_version
        File renamed_fasta = mt.renamed_fasta
        File map_file = mt.map_file
        # metaT_ReadCounts
        File count_table = mt.count_table
        File? count_ig = mt.count_ig
        File? count_log = mt.count_log
        File readcount_info = mt.readcount_info
        # output tables
        File gff_json = mt.gff_json
        File rc_json = mt.rc_json
        File gff_rc_json = mt.gff_rc_json
        File cds_json = mt.cds_json
        File sense_json = mt.sense_json
        File anti_json = mt.anti_json
        File top100_json = mt.top100_json
        File sorted_json = mt.sorted_json
        File sorted_tsv = mt.sorted_tsv
    }

    
}
