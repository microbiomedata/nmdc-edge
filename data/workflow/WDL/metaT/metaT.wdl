# metaT workflow wrapper
version 1.0

# import "https://raw.githubusercontent.com/microbiomedata/metaT_ReadsQC/v0.0.7/rqcfilter.wdl" as readsqc
import "https://raw.githubusercontent.com/microbiomedata/metaT_Assembly/v0.0.2/metaT_assembly.wdl" as assembly
import "https://raw.githubusercontent.com/microbiomedata/mg_annotation/v1.1.4/annotation_full.wdl" as annotation
import "https://raw.githubusercontent.com/microbiomedata/metaT_ReadCounts/v0.0.4/readcount.wdl" as readcounts
import "./metat_tasks.wdl" as tasks

import "https://raw.githubusercontent.com/microbiomedata/metaT_ReadsQC/7-readqc-not-always-specifying-the-correct-output-file/rqcfilter.wdl" as readsqc


workflow nmdc_metat {

    input {
        String  project_id
        File    input_file
        File?   input_fq1
        File?   input_fq2
        Boolean input_interleaved = false
        # Array[String] input_files
        String  strand_type = " "
        String  prefix = sub(project_id, ":", "_")
        String  container = "microbiomedata/bbtools:38.96"
        String  tj_container =  "microbiomedata/meta_t@sha256:f18ff86c78909f70c7b6b8aa3a2d5c521800e10e0e270a9aa7fce6f383c224ba"
        String  fi_container="scanon/nmdc-meta:v0.0.1"
        Int     rqc_mem = 180
        Int     rqc_thr = 64
        Int     anno_mem = 120
        Int     anno_thr = 16
    }

     if (!input_interleaved) {
         call tasks.make_interleaved as int  {
            input:
            fastq1 = input_fq1,
	        fastq2 = input_fq2,
            pref = prefix,
	        container=container
           } 
    }

    call readsqc.metaTReadsQC as qc {
        input:
        proj = project_id,
        input_files = if (input_interleaved) then [input_file] else [int.out_fastq],
        rqc_mem = rqc_mem,
        rqc_thr = rqc_thr
    }

    call assembly.metatranscriptome_assy as asse{
        input:
        # single file to array of files
        input_files = [qc.filtered_final],
        proj_id = project_id
    }

    call annotation.annotation as anno{
        input:
        proj = project_id,
        input_file = asse.final_contigs,
        imgap_project_id = project_id,
        additional_memory = anno_mem,
        additional_threads = anno_thr
    }

    call readcounts.readcount as rc{
        input:
        bam = asse.final_bam,
        gff = anno.functional_gff,
        map = anno.map_file,
        rna_type = strand_type,
        proj_id = project_id

    }

    call tasks.rctojson as tj{
        input:
        readcount = rc.count_table,
        gff = anno.functional_gff,
        prefix = prefix,
        container = tj_container
    }

    call tasks.finish_metat as fi {
        input: 
        container=fi_container,
        proj = project_id, 
        filtered = qc.filtered_final,
        filtered_stats = qc.filtered_stats_final,
        filtered_stats2 = qc.filtered_stats2_final,
        filtered_ribo = qc.filtered_ribo_final,
        rqc_info = qc.rqc_info,
        tar_bam = asse.final_tar_bam,
        contigs = asse.final_contigs,
        scaffolds = asse.final_scaffolds,
        asse_log = asse.final_log,
	    readlen = asse.final_readlen,
        sam = asse.final_sam,
        bam = asse.final_bam,
        bamidx = asse.final_bamidx,
        cov = asse.final_cov,
        asmstats = asse.asmstats,
        asse_info  = asse.info_file,
        proteins_faa = anno.proteins_faa,
        structural_gff = anno.structural_gff,
        ko_ec_gff = anno.ko_ec_gff,
        gene_phylogeny_tsv = anno.gene_phylogeny_tsv,
        functional_gff = anno.functional_gff,
        ko_tsv = anno.ko_tsv,
        ec_tsv = anno.ec_tsv,
        lineage_tsv = anno.lineage_tsv,
        stats_tsv = anno.stats_tsv,
        stats_json = anno.stats_json,
        cog_gff = anno.cog_gff,
        pfam_gff = anno.pfam_gff,
        tigrfam_gff = anno.tigrfam_gff,
        smart_gff = anno.smart_gff,
        supfam_gff = anno.supfam_gff,
        cath_funfam_gff = anno.cath_funfam_gff,
        crt_gff = anno.crt_gff,
        genemark_gff = anno.genemark_gff,
        prodigal_gff = anno.prodigal_gff,
        trna_gff = anno.trna_gff,
        rfam_gff = anno.final_rfam_gff,
        product_names_tsv = anno.product_names_tsv,
        crt_crisprs = anno.crt_crisprs,
        imgap_version = anno.imgap_version,
        renamed_fasta = anno.renamed_fasta,
        map_file = anno.map_file,
        count_table = rc.count_table,
        count_ig = rc.count_ig,
        count_log = rc.count_log,
        readcount_info = rc.info_file,
        gff_json = tj.gff_json,
        rc_json = tj.rc_json,
        gff_rc_json = tj.gff_rc_json,
		cds_json = tj.cds_json,
		sense_json = tj.sense_json,
		anti_json = tj.anti_json,
        top100_json = tj.top100_json,
		sorted_json = tj.sorted_json,
        sorted_tsv = tj.sorted_tsv
 
  }

    output{ 
        # metaT_ReadsQC
        File filtered_final = fi.final_filtered
        File filtered_stats_final = fi.final_filtered_stats
        File filtered_stats2_final = fi.final_filtered_stats2
        File rqc_info = fi.final_rqc_info
        File rqc_stats = fi.final_rqc_stats
        File filtered_ribo_final = fi.final_filtered_ribo
        # metaT_Assembly
        File final_tar_bam = fi.final_tar_bam
        File final_contigs = fi.final_contigs
        File final_scaffolds = fi.final_scaffolds
        File final_asse_log = fi.final_asm_log
	    File final_readlen = fi.final_readlen
        File final_sam = fi.final_sam
        File final_bam = fi.final_bam
        File final_bamidx = fi.final_bamidx
        File final_cov = fi.final_cov
        File final_asmstats = fi.final_asmstats
        File asse_info  = fi.final_asm_info
        # mg_annotation
        File proteins_faa = fi.final_proteins_faa
        File structural_gff = fi.final_structural_gff
        File ko_ec_gff = fi.final_ko_ec_gff
        File gene_phylogeny_tsv = fi.final_gene_phylogeny_tsv
        File functional_gff = fi.final_functional_gff
        File ko_tsv = fi.final_ko_tsv
        File ec_tsv = fi.final_ec_tsv
        File lineage_tsv = fi.final_lineage_tsv
        File stats_tsv = fi.final_stats_tsv
        File stats_json = fi.final_stats_json
        File cog_gff = fi.final_cog_gff
        File pfam_gff = fi.final_pfam_gff
        File tigrfam_gff = fi.final_tigrfam_gff
        File smart_gff = fi.final_smart_gff
        File supfam_gff = fi.final_supfam_gff
        File cath_funfam_gff = fi.final_cath_funfam_gff
        File crt_gff = fi.final_crt_gff
        File genemark_gff = fi.final_genemark_gff
        File prodigal_gff = fi.final_prodigal_gff
        File trna_gff = fi.final_trna_gff
        File final_rfam_gff = fi.final_rfam_gff
        File product_names_tsv = fi.final_product_names_tsv
        File crt_crisprs = fi.final_crt_crisprs
        File imgap_version = fi.final_imgap_version
        File renamed_fasta = fi.final_renamed_fasta
        File map_file = fi.final_map_file
        # metaT_ReadCounts
        File count_table = fi.final_count_table
        File? count_ig = fi.final_count_ig
        File? count_log = fi.final_count_log
        File readcount_info = fi.final_readcount_info
        # output tables
        File gff_json = fi.final_gff_json
        File rc_json = fi.final_rc_json
        File gff_rc_json = fi.final_gff_rc_json
		File cds_json = fi.final_cds_json
		File sense_json = fi.final_sense_json
		File anti_json = fi.final_anti_json
        File top100_json = fi.final_top100_json
		File sorted_json = fi.final_sorted_json
        File sorted_tsv = fi.final_sorted_tsv
    }

    parameter_meta {
        project_id: "Project ID string.  This will be appended to the gene ids"
        input_file: "File path to raw fastq, must be interleaved and gzipped."
        strand_type: "RNA strandedness, optional, can be left out / blank, 'aRNA', or 'non_stranded_RNA'"
        input_interleaved: "Optional boolean to specify whether input files are interleaved. Default false."
        input_fq1: "Optional input file path if files need to be interleaved (same as 'input_file')."
        input_fq2: "Optional second input file path if files need to be interleaved"
    }
    
}