import "structural-annotation.wdl" as sa
import "functional-annotation.wdl" as fa

workflow annotation {
  File    imgap_input_fasta
  String  imgap_project_id="GaXXXXXXX_contigs.fna"
  String  database_location="/cromwell_root/database"
  String  imgap_project_type="metagenome"
  Int     additional_threads=16
  String  container="bfoster1/img-omics:0.1.9"

  # structural annotation
  Boolean sa_execute=true

  # functional annotation
  Boolean fa_execute=true

  call split {
    input: infile=imgap_input_fasta,
           container=container
  }

  scatter(pathname in split.files) {
    if(sa_execute) {
      call sa.s_annotate {
        input:
          cmzscore = split.cmzscore,
          imgap_input_fasta = imgap_input_fasta,
          imgap_input_fasta = pathname,
          imgap_project_id = imgap_project_id,
          additional_threads = additional_threads,
          imgap_project_type = imgap_project_type,
          database_location = database_location,
          container=container
      }
    }

    if(fa_execute) {
      call fa.f_annotate {
        input:
          approx_num_proteins = split.zscore,
          imgap_project_id = imgap_project_id,
          imgap_project_type = imgap_project_type,
          additional_threads = additional_threads,
          input_fasta = s_annotate.proteins,
          database_location = database_location,
          sa_gff = s_annotate.gff,
          container=container
      }
    }
  }
  call merge_outputs {
    input:
       project_id = imgap_project_id,
       product_name_tsvs = f_annotate.product_name_tsv,
       structural_gffs=s_annotate.gff,
       functional_gffs=f_annotate.gff,
       ko_tsvs = f_annotate.ko_tsv,
       ec_tsvs = f_annotate.ec_tsv,
       phylo_tsvs =  f_annotate.phylo_tsv,
       proteins = s_annotate.proteins,
       ko_ec_gffs = f_annotate.ko_ec_gff,
       cog_gffs = f_annotate.cog_gff,
       pfam_gffs = f_annotate.pfam_gff,
       tigrfam_gffs = f_annotate.tigrfam_gff,
       smart_gffs = f_annotate.smart_gff,
       supfam_gffs = f_annotate.supfam_gff,
       cath_funfam_gffs = f_annotate.cath_funfam_gff,
       cog_domtblouts = f_annotate.cog_domtblout,
       pfam_domtblouts = f_annotate.pfam_domtblout,
       tigrfam_domtblouts = f_annotate.tigrfam_domtblout,
       smart_domtblouts = f_annotate.smart_domtblout,
       supfam_domtblouts = f_annotate.supfam_domtblout,
       cath_funfam_domtblouts = f_annotate.cath_funfam_domtblout,
       crt_crisprs_s = s_annotate.crisprs,
       crt_gffs = s_annotate.crt_gff,
       genemark_gffs = s_annotate.genemark_gff,
       prodigal_gffs = s_annotate.prodigal_gff,
       trna_gffs = s_annotate.trna_gff,
       misc_bind_misc_feature_regulatory_gffs = s_annotate.misc_bind_misc_feature_regulatory_gff,
       rrna_gffs = s_annotate.rrna_gff,
       ncrna_tmrna_gffs = s_annotate.ncrna_tmrna_gff,
       container=container
  }
  call final_stats {
    input:
       project_id = imgap_project_id,
       structural_gff = merge_outputs.structural_gff,
       input_fasta = imgap_input_fasta,
       container=container
  }
  output {
    File? proteins_faa = merge_outputs.proteins_faa
    File? structural_gff = merge_outputs.structural_gff
    File? ko_ec_gff = merge_outputs.ko_ec_gff
    File? gene_phylogeny_tsv = merge_outputs.gene_phylogeny_tsv
    File? functional_gff = merge_outputs.functional_gff
    File? ko_tsv = merge_outputs.ko_tsv
    File? ec_tsv = merge_outputs.ec_tsv
    File? stats_tsv = final_stats.tsv
    File? stats_json = final_stats.json
    File? cog_gff = merge_outputs.cog_gff
    File? pfam_gff = merge_outputs.pfam_gff
    File? tigrfam_gff = merge_outputs.tigrfam_gff
    File? smart_gff = merge_outputs.smart_gff
    File? supfam_gff = merge_outputs.supfam_gff
    File? cath_funfam_gff = merge_outputs.cath_funfam_gff
    File? crt_gff = merge_outputs.crt_gff
    File? genemark_gff = merge_outputs.genemark_gff
    File? prodigal_gff = merge_outputs.prodigal_gff
    File? trna_gff = merge_outputs.trna_gff
    File? misc_bind_misc_feature_regulatory_gff = merge_outputs.misc_bind_misc_feature_regulatory_gff
    File? rrna_gff = merge_outputs.rrna_gff
    File? ncrna_tmrna_gff = merge_outputs.ncrna_tmrna_gff
    File? proteins_cog_domtblout = merge_outputs.proteins_cog_domtblout
    File? proteins_pfam_domtblout = merge_outputs.proteins_pfam_domtblout
    File? proteins_tigrfam_domtblout = merge_outputs.proteins_tigrfam_domtblout
    File? proteins_smart_domtblout = merge_outputs.proteins_smart_domtblout
    File? proteins_supfam_domtblout = merge_outputs.proteins_supfam_domtblout
    File? proteins_cath_funfam_domtblout = merge_outputs.proteins_cath_funfam_domtblout
    File? product_names_tsv = merge_outputs.product_names_tsv
    File? crt_crisprs = merge_outputs.crt_crisprs
  }
  parameter_meta {
    imgap_input_fasta: "assembled contig file in fasta format"
    additional_threads: "optional for number of threads: 16"
    database_location: "File path to database. This should be /refdata for container runs"
    imgap_project_id: "Project ID string.  This will be appended to the gene ids"
    imgap_project_type: "Project Type (isolate, metagenome) defaults to metagenome"
    container: "Default container to use"
  }
  meta {
    author: "Brian Foster"
    email: "bfoster@lbl.gov"
    version: "1.0.0"
  }


}

task split{
   File infile
   String blocksize=100
   String zfile="zscore.txt"
   String cmzfile="cmzscore.txt"
   String container

   command{
     set -euo pipefail
     /opt/omics/bin/split.py ${infile} ${blocksize} .
     echo $(egrep -v "^>" ${infile} | tr -d '\n' | wc -m) / 500 | bc > ${zfile}
     echo "scale=6; ($(grep -v '^>' ${infile} | tr -d '\n' | wc -m) * 2) / 1000000" | bc -l > ${cmzfile}
   }

   output{
     Array[File] files = read_lines('splits_out.fof')
     String zscore = read_string(zfile)
     String cmzscore = read_string(cmzfile)
   }
   runtime {
     memory: "120 GiB"
     cpu:  16
     maxRetries: 1
     docker: container
   }
}


task merge_outputs {
  String  project_id
  Array[File?] structural_gffs
  Array[File?] functional_gffs
  Array[File?] ko_tsvs
  Array[File?] ec_tsvs
  Array[File?] phylo_tsvs
  Array[File?] proteins
  Array[File?] ko_ec_gffs
  Array[File?] cog_gffs
  Array[File?] pfam_gffs
  Array[File?] tigrfam_gffs
  Array[File?] smart_gffs
  Array[File?] supfam_gffs
  Array[File?] cath_funfam_gffs
  Array[File?] cog_domtblouts
  Array[File?] pfam_domtblouts
  Array[File?] tigrfam_domtblouts
  Array[File?] smart_domtblouts
  Array[File?] supfam_domtblouts
  Array[File?] cath_funfam_domtblouts
  Array[File?] product_name_tsvs
  Array[File?] crt_crisprs_s
  Array[File?] crt_gffs
  Array[File?] genemark_gffs
  Array[File?] prodigal_gffs
  Array[File?] trna_gffs
  Array[File?] misc_bind_misc_feature_regulatory_gffs
  Array[File?] rrna_gffs
  Array[File?] ncrna_tmrna_gffs
  String container

  command {
     cat ${sep=" " structural_gffs} > "${project_id}_structural_annotation.gff"
     cat ${sep=" " functional_gffs} > "${project_id}_functional_annotation.gff"
     cat ${sep=" " ko_tsvs} >  "${project_id}_ko.tsv"
     cat ${sep=" " ec_tsvs} >  "${project_id}_ec.tsv"
     cat ${sep=" " phylo_tsvs} > "${project_id}_gene_phylogeny.tsv"
     cat ${sep=" " proteins} > "${project_id}.faa"
     cat ${sep=" " ko_ec_gffs} > "${project_id}_ko_ec.gff"
     cat ${sep=" " cog_gffs} > "${project_id}_cog.gff"
     cat ${sep=" " pfam_gffs} > "${project_id}_pfam.gff"
     cat ${sep=" " tigrfam_gffs} > "${project_id}_tigrfam.gff"
     cat ${sep=" " smart_gffs} > "${project_id}_smart.gff"
     cat ${sep=" " supfam_gffs} > "${project_id}_supfam.gff"
     cat ${sep=" " cath_funfam_gffs} > "${project_id}_cath_funfam.gff"
     cat ${sep=" " crt_gffs} > "${project_id}_crt.gff"
     cat ${sep=" " genemark_gffs} > "${project_id}_genemark.gff"
     cat ${sep=" " prodigal_gffs} > "${project_id}_prodigal.gff"
     cat ${sep=" " trna_gffs} > "${project_id}_trna.gff"
     cat ${sep=" " misc_bind_misc_feature_regulatory_gffs} > "${project_id}_rfam_misc_bind_misc_feature_regulatory.gff"
     cat ${sep=" " rrna_gffs} > "${project_id}_rfam_rrna.gff"
     cat ${sep=" " ncrna_tmrna_gffs} > "${project_id}_rfam_ncrna_tmrna.gff"

     cat ${sep=" " cog_domtblouts} > "${project_id}_proteins.cog.domtblout"
     cat ${sep=" " pfam_domtblouts} > "${project_id}_proteins.pfam.domtblout"
     cat ${sep=" " tigrfam_domtblouts} > "${project_id}_proteins.tigrfam.domtblout"
     cat ${sep=" " smart_domtblouts} > "${project_id}_proteins.smart.domtblout"
     cat ${sep=" " supfam_domtblouts} > "${project_id}_proteins.supfam.domtblout"
     cat ${sep=" " cath_funfam_domtblouts} > "${project_id}_proteins.cath_funfam.domtblout"

     cat ${sep=" " product_name_tsvs} > "${project_id}_product_names.tsv"
     cat ${sep=" " crt_crisprs_s} > "${project_id}_crt.crisprs"
  }
  output {
    File functional_gff = "${project_id}_functional_annotation.gff"
    File structural_gff = "${project_id}_structural_annotation.gff"
    File ko_tsv = "${project_id}_ko.tsv"
    File ec_tsv = "${project_id}_ec.tsv"
    File gene_phylogeny_tsv = "${project_id}_gene_phylogeny.tsv"
    File proteins_faa = "${project_id}.faa"
    File ko_ec_gff = "${project_id}_ko_ec.gff"
    File cog_gff = "${project_id}_cog.gff"
    File pfam_gff = "${project_id}_pfam.gff"
    File tigrfam_gff = "${project_id}_tigrfam.gff"
    File smart_gff = "${project_id}_smart.gff"
    File supfam_gff = "${project_id}_supfam.gff"
    File cath_funfam_gff = "${project_id}_cath_funfam.gff"
    File crt_gff = "${project_id}_crt.gff"
    File genemark_gff = "${project_id}_genemark.gff"
    File prodigal_gff = "${project_id}_prodigal.gff"
    File trna_gff = "${project_id}_trna.gff"
    File misc_bind_misc_feature_regulatory_gff = "${project_id}_rfam_misc_bind_misc_feature_regulatory.gff"
    File rrna_gff = "${project_id}_rfam_rrna.gff"
    File ncrna_tmrna_gff = "${project_id}_rfam_ncrna_tmrna.gff"
    File proteins_cog_domtblout = "${project_id}_proteins.cog.domtblout"
    File proteins_pfam_domtblout = "${project_id}_proteins.pfam.domtblout"
    File proteins_tigrfam_domtblout = "${project_id}_proteins.tigrfam.domtblout"
    File proteins_smart_domtblout = "${project_id}_proteins.smart.domtblout"
    File proteins_supfam_domtblout = "${project_id}_proteins.supfam.domtblout"
    File proteins_cath_funfam_domtblout = "${project_id}_proteins.cath_funfam.domtblout"
    File product_names_tsv = "${project_id}_product_names.tsv"
    File crt_crisprs = "${project_id}_crt.crisprs"
  }
  runtime {
    memory: "2 GiB"
    cpu:  4
    maxRetries: 1
    docker: container
  }

# TODO:
#contig_names_mapping_tsv
#Coverage_file_cov

}

task final_stats {
  String bin="/opt/omics/bin/structural_annotation/gff_and_final_fasta_stats.py"
  File   input_fasta
  String project_id
  String fna="${project_id}_contigs.fna"
  File   structural_gff
  String container

  command {
    set -euo pipefail
    ln ${input_fasta} ${fna}
    ${bin} ${fna} ${structural_gff}
  }

  output {
    File tsv = "${project_id}_structural_annotation_stats.tsv"
    File json = "${project_id}_structural_annotation_stats.json"
  }

  runtime {
    time: "0:10:00"
    memory: "86G"
    docker: container
  }
}

