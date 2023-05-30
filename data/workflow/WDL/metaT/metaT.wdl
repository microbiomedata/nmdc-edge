import "metat_tasks.wdl" as mt
import "rqcfilter.wdl" as rqc
import "additional_qc.wdl" as aq
import "metat_assembly.wdl" as ma
import "map_bbmap.wdl" as bb
import "annotation_full.wdl" as awf
import "feature_counts.wdl" as fc
import "calc_scores.wdl" as cs
import "to_json.wdl" as tj

workflow nmdc_metat {
    String  metat_container = "migun/meta_t2:latest"
    String  featcounts_container = "mbabinski17/featcounts:dev"
    String  feature_types_container = "mbabinski17/rpkm_sort:0.0.5"
    String  proj
    String informed_by
    String activity_id
    String git_url = "https://data.microbiomedata.org/data/"
    String url_root = "https://github.com/microbiomedata/mg_annotation/releases/tag/0.1"
    String resource
    File    input_file
    String  outdir 
    String  database  
    Int threads = 64
    File metat_folder 
    Boolean input_interleaved = false
    File? input_fq1
    File? input_fq2

    if (!input_interleaved) {
         call mt.make_interleaved as int  {
            input:
            input1 = input_fq1,
	    input2 = input_fq2,
            pref = activity_id,
	    container="microbiomedata/bbtools:38.96"
           } 
    }

    call mt.stage as stage {
    input: input_file=if input_interleaved then input_file else int.out_fastq,
           proj=proj,
           container=metat_container
   }


    
    call rqc.jgi_rqcfilter as qc {
    input: input_files=[stage.read],
           outdir="${outdir}/qa/",
           threads=threads,
           memory="64G",
           database=database
    }

    call ma.megahit_assembly as asm {
    input: rqc_clean_reads = qc.filtered,
           assem_out_fdr = "${outdir}/assembly/",
           assem_out_prefix = sub(proj, ":", "_"),
           no_of_cpus = threads,
           DOCKER = metat_container
  }

    call bb.bbmap_mapping as bbm{
        input:rna_clean_reads = qc.filtered,
        no_of_cpus = 16,
        assembly_fna = asm.assem_fna_file
    }
    call awf.annotation as iap {
    input: imgap_project_id=stage.pref,
           imgap_input_fasta=asm.assem_fna_file,
           database_location="/databases/img/",
           #additional_threads=threads

    }
	
    call fc.parse_intergenic as pint {
		input: annotation_gff = iap.functional_gff, 
		DOCKER = feature_types_container
	}
    call mt.clean_gff as dcg{
		input:gff_file_path = pint.filtered_intergenic_gff,
		DOCKER = metat_container

	}

    call mt.extract_feats as ef {
		input:gff_file_path = dcg.cln_gff_fl,
		DOCKER = metat_container
	}

    call mt.create_gffdb{
		input:gff_file_path = dcg.cln_gff_fl,
		DOCKER = metat_container
	}
    
    scatter (feat in ef.feats_in_gff) {
		call fc.featurecount{
		input: no_of_cpu = threads,
		project_name = sub(proj, ":", "_"),
		gff_file_path = dcg.cln_gff_fl,
		bam_file_path = bbm.map_bam,
		name_of_feat = feat,
		DOCKER = featcounts_container
		}
		call cs.cal_scores{
		input: project_name = sub(proj, ":", "_"),
		name_of_feat = feat,
		fc_file = featurecount.ct_tbl,
		DOCKER = metat_container
		}
        call tj.convtojson as tdc{
		input:gff_file_path = dcg.cln_gff_fl,
		fasta_file_name = asm.assem_fna_file,
		rd_count_fn = featurecount.ct_tbl,
		pkm_sc_fn = cal_scores.sc_tbl,
		name_of_feat = feat,
		gff_db_fn = create_gffdb.gff_db_fn,
                py_pack_path = metat_folder + "/pyp_metat",
		DOCKER = metat_container
		}
	
                call cs.cal_scores as cs2{
                input: project_name = sub(proj, ":", "_"),
                name_of_feat = feat,
                fc_file = featurecount.ct_tbl2,
                DOCKER = metat_container
                }
        call tj.convtojson as tdc2{
                input:gff_file_path = dcg.cln_gff_fl,
                fasta_file_name = asm.assem_fna_file,
                rd_count_fn = featurecount.ct_tbl2,
                pkm_sc_fn = cs2.sc_tbl,
                name_of_feat = feat,
                gff_db_fn = create_gffdb.gff_db_fn,
                py_pack_path = metat_folder + "/pyp_metat",
                DOCKER = metat_container
                }
        }
    call mt.collect_output as mdo {
		input: out_files = tdc.out_json_file,
        prefix=sub(proj, ":", "_"),
		DOCKER = metat_container
	}

    call mt.collect_output2 as mdo2 {
                input: out_files = tdc2.out_json_file,
        prefix=sub(proj, ":", "_"),
                DOCKER = metat_container
        }
    call fc.add_feature_types as aft{
	input: sense = mdo.out_json_file,
	       antisense = mdo2.out_json_file2,
	       proj = sub(proj, ":", "_"),
	       DOCKER =  feature_types_container
	}
    call mt.finish_metat as mfm {
    input: container="microbiomedata/workflowmeta:1.0.5.1",
           start=stage.start,
           resource=resource,
           proj=proj,
	   informed_by=informed_by,
           url_root=url_root,
           git_url=git_url,
           read = stage.read,
           filtered = qc.filtered[0],
           filtered_stats = qc.stats[0],
	   filtered_stats2 = qc.stats2[0],
           fasta=asm.assem_fna_file,
           bbm_bam=bbm.map_bam,
	   covstats=bbm.covstats,
           out_json=aft.filtered_sense_json,
	   out_json2=aft.filtered_antisense_json,
	   sorted_features=aft.full_features_tsv,
           top100=aft.top100,
	   stats_tsv=iap.stats_tsv,
           stats_json=iap.stats_json,
           proteins_faa=iap.proteins_faa,
           functional_gff=iap.functional_gff,
           structural_gff=iap.structural_gff,
           ko_tsv=iap.ko_tsv,
           ec_tsv=iap.ec_tsv,
           cog_gff=iap.cog_gff,
           pfam_gff=iap.pfam_gff,
           tigrfam_gff=iap.tigrfam_gff,
           smart_gff=iap.smart_gff,
           supfam_gff=iap.supfam_gff,
           cath_funfam_gff=iap.cath_funfam_gff,
           ko_ec_gff=iap.ko_ec_gff,
           gene_phylogeny_tsv=iap.gene_phylogeny_tsv,
	   cog_domtblout=iap.proteins_cog_domtblout,
 	   pfam_domtblout=iap.proteins_pfam_domtblout,
 	   tigrfam_domtblout=iap.proteins_tigrfam_domtblout,
 	   smart_domtblout=iap.proteins_smart_domtblout,
 	   supfam_domtblout=iap.proteins_supfam_domtblout,
 	   cath_funfam_domtblout=iap.proteins_cath_funfam_domtblout,
 	   product_names_tsv=iap.product_names_tsv,
 	   crt_crisprs=iap.crt_crisprs,
 	   crt_gff=iap.crt_gff,
 	   genemark_gff=iap.genemark_gff,
 	   prodigal_gff=iap.prodigal_gff,
 	   trna_gff=iap.trna_gff,
 	   misc_bind_misc_feature_regulatory_gff=iap.misc_bind_misc_feature_regulatory_gff,
 	   rrna_gff=iap.rrna_gff,
  	   ncrna_tmrna_gff=iap.ncrna_tmrna_gff,
           outdir=outdir
  }

    meta {
        author: "Migun Shakya, B10, LANL"
        email: "migun@lanl.gov"
        version: "0.0.3"
    }

}
