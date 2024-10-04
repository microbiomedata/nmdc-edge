import "structural-annotation.wdl" as sa
import "functional-annotation.wdl" as fa

workflow annotation {
  File    imgap_input_fasta
  String  imgap_project_id="GaXXXXXXX_contigs.fna"
  String database_location="/cromwell_root/database"
  String  imgap_project_type="metagenome"
  Int     additional_threads=16

  # structural annotation
  Boolean sa_execute=true
  # functional annotation
  Boolean fa_execute=true

  call split {input: infile=imgap_input_fasta}
  scatter(pathname in split.files) {
    if(sa_execute) {
      call sa.s_annotate {
        input:
          imgap_input_fasta = pathname,
          imgap_project_id = imgap_project_id,
          additional_threads = additional_threads,
          imgap_project_type = imgap_project_type,
          database_location = database_location,
          rfam_execute = false
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
          sa_gff = s_annotate.gff
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
       crt_crisprs_s = s_annotate.crisprs
  }
  call final_stats {
    input:
       project_id = imgap_project_id,
       structural_gff = merge_outputs.structural_gff,
       input_fasta = imgap_input_fasta
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
    File? cog_gff = merge_outputs.cog_gff
    File? pfam_gff = merge_outputs.pfam_gff
    File? tigrfam_gff = merge_outputs.tigrfam_gff
    File? smart_gff = merge_outputs.smart_gff
    File? supfam_gff = merge_outputs.supfam_gff
    File? cath_funfam_gff = merge_outputs.cath_funfam_gff
    File? proteins_cog_domtblout = merge_outputs.proteins_cog_domtblout
    File? proteins_pfam_domtblout = merge_outputs.proteins_pfam_domtblout
    File? proteins_tigrfam_domtblout = merge_outputs.proteins_tigrfam_domtblout
    File? proteins_smart_domtblout = merge_outputs.proteins_smart_domtblout
    File? proteins_supfam_domtblout = merge_outputs.proteins_supfam_domtblout
    File? proteins_cath_funfam_domtblout = merge_outputs.proteins_cath_funfam_domtblout
    File? product_names_tsv = merge_outputs.product_names_tsv
    File? crt_crisprs = merge_outputs.crt_crisprs
  }

}

task split{
   File infile
   String blocksize=10
   String zfile="zscore.txt"

   command{
     /opt/omics/bin/split.py ${infile} ${blocksize} .
     echo $(egrep -v "^>" ${infile} | tr -d '\n' | wc -m) / 500 | bc > ${zfile}
   }

   output{
     Array[File] files = read_lines('splits_out.fof')
     String zscore = read_string(zfile)
   }
   runtime {
     memory: "120 GiB"
     cpu:  16
     maxRetries: 1
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

    File proteins_cog_domtblout = "${project_id}_proteins.cog.domtblout"
    File proteins_pfam_domtblout = "${project_id}_proteins.pfam.domtblout"
    File proteins_tigrfam_domtblout = "${project_id}_proteins.tigrfam.domtblout"
    File proteins_smart_domtblout = "${project_id}_proteins.smart.domtblout"
    File proteins_supfam_domtblout = "${project_id}_proteins.supfam.domtblout"
    File proteins_cath_funfam_domtblout = "${project_id}_proteins.cath_funfam.domtblout"
    File product_names_tsv = "${project_id}_product_names.tsv"
    File crt_crisprs = "${project_id}_crt.crisprs"
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

  command {
    ln ${input_fasta} ${fna}
    ${bin} ${fna} ${structural_gff}
  }

  output {
    File tsv = "${project_id}_structural_annotation_stats.tsv"
  }

  runtime {
    time: "0:10:00"
    memory: "86G"
  }
}

