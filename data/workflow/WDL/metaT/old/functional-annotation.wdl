workflow f_annotate {
  String  imgap_project_id
  String  imgap_project_type
  Int     additional_threads
  File?    input_contigs_fasta
  File    input_fasta
  String  database_location
  Boolean ko_ec_execute=true
  String  ko_ec_img_nr_db="${database_location}"+"IMG-NR/20190607/img_nr"
  String  ko_ec_md5_mapping="${database_location}"+"IMG-NR/20190607/md5Hash2Data.txt"
  String  ko_ec_taxon_to_phylo_mapping="${database_location}"+"IMG-NR/20190607/taxonOid2Taxonomy.txt"
  String  lastal_bin="/opt/omics/bin/lastal"
  String  selector_bin="/opt/omics/bin/functional_annotation/lastal_img_nr_ko_ec_gene_phylo_hit_selector.py"
  Boolean smart_execute=true
  Int?    par_hmm_inst
  Int?    approx_num_proteins
  String  smart_db="${database_location}"+"SMART/01_06_2016/SMART.hmm"
  String  hmmsearch_bin="/opt/omics/bin/hmmsearch"
  String  frag_hits_filter_bin="/opt/omics/bin/functional_annotation/hmmsearch_fragmented_hits_filter.py"
  Boolean cog_execute=true
  String  cog_db="${database_location}"+"COG/HMMs/2003/COG.hmm"
  Boolean tigrfam_execute=true
  String  tigrfam_db="${database_location}"+"TIGRFAM/v15.0/TIGRFAM.hmm"
  String  hit_selector_bin="/opt/omics/bin/functional_annotation/hmmsearch_hit_selector.py"
  Boolean superfam_execute=true
  String  superfam_db="${database_location}"+"SuperFamily/v1.75/supfam.hmm"
  Boolean pfam_execute=true
  String  pfam_db="${database_location}"+"Pfam/Pfam-A-LATEST/Pfam-A.hmm"
  String  pfam_claninfo_tsv="${database_location}"+"Pfam/Pfam-A-LATEST/Pfam-A.clans.tsv"
  String  pfam_clan_filter="/opt/omics/bin/functional_annotation/pfam_clan_filter.py"
  Boolean cath_funfam_execute=true
  String  cath_funfam_db="${database_location}"+"Cath-FunFam/latest/funfam.hmm"
  Boolean signalp_execute=true
  String  signalp_gram_stain="GRAM_STAIN"
  String  signalp_bin="/opt/omics/bin/signalp"
  Boolean tmhmm_execute=true
  String  tmhmm_model="/opt/omics/programs/tmhmm-2.0c/lib/TMHMM2.0.model"
  String  tmhmm_decode="/opt/omics/bin/decodeanhmm"
  String  tmhmm_decode_parser="/opt/omics/bin/functional_annotation/decodeanhmm_parser.py"
  File    sa_gff
  String  product_assign_bin="/opt/omics/bin/functional_annotation/assign_product_names_and_create_fa_gff.py"
  String  product_names_mapping_dir="${database_location}"+"Product_Name_Mappings/latest"
  String  container
  String  hmm_container="scanon/im-hmmsearch:v0.0.0"
  String  last_container="scanon/im-last:v0.0.1"

  if(ko_ec_execute) {
    call ko_ec {
      input:
        project_id = imgap_project_id,
        project_type = imgap_project_type,
        input_fasta = input_fasta,
        threads = additional_threads,
        nr_db = ko_ec_img_nr_db,
        md5 = ko_ec_md5_mapping,
        phylo = ko_ec_taxon_to_phylo_mapping,
        lastal = lastal_bin,
        selector = selector_bin,
        container=last_container
    }
  }
  if(smart_execute) {
    call smart {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        smart_db = smart_db,
        hmmsearch = hmmsearch_bin,
        frag_hits_filter = frag_hits_filter_bin,
        container=hmm_container
    }
  }
  if(cog_execute) {
    call cog {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        cog_db = cog_db,
        hmmsearch = hmmsearch_bin,
        frag_hits_filter = frag_hits_filter_bin,
        container=hmm_container
    }
  }
  if(tigrfam_execute) {
    call tigrfam {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        tigrfam_db = tigrfam_db,
        hmmsearch = hmmsearch_bin,
        hit_selector = hit_selector_bin,
        container=hmm_container
    }
  }
  if(superfam_execute) {
    call superfam {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        superfam_db = superfam_db,
        hmmsearch = hmmsearch_bin,
        frag_hits_filter = frag_hits_filter_bin,
        container=hmm_container
    }
  }
  if(pfam_execute) {
    call pfam {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        pfam_db = pfam_db,
        pfam_claninfo_tsv = pfam_claninfo_tsv,
        pfam_clan_filter = pfam_clan_filter,
        hmmsearch = hmmsearch_bin,
        container=hmm_container
    }
  }
  if(cath_funfam_execute) {
    call cath_funfam {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        threads = additional_threads,
        par_hmm_inst = par_hmm_inst,
        approx_num_proteins = approx_num_proteins,
        cath_funfam_db = cath_funfam_db,
        hmmsearch = hmmsearch_bin,
        frag_hits_filter = frag_hits_filter_bin,
        container=hmm_container
    }
  }
  if(imgap_project_type == "isolate" && signalp_execute) {
    call signalp {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        gram_stain = signalp_gram_stain,
        signalp = signalp_bin,
        container=container
    }
  }
  if(imgap_project_type == "isolate" && tmhmm_execute) {
    call tmhmm {
      input:
        project_id = imgap_project_id,
        input_fasta = input_fasta,
        model = tmhmm_model,
        decode = tmhmm_decode,
        decode_parser = tmhmm_decode_parser,
        container=container
    }
  }
  if(true){
    call product_name {
      input:
        project_id = imgap_project_id,
        sa_gff = sa_gff,
        product_assign = product_assign_bin,
        map_dir = product_names_mapping_dir,
        ko_ec_gff = ko_ec.gff,
        smart_gff = smart.gff,
        cog_gff = cog.gff,
        tigrfam_gff = tigrfam.gff,
        supfam_gff = superfam.gff,
        pfam_gff = pfam.gff,
        cath_funfam_gff = cath_funfam.gff,
        signalp_gff = signalp.gff,
        tmhmm_gff = tmhmm.gff,
        container=container
    }
  }
  output {
    File? gff = product_name.gff
    File? product_name_tsv = product_name.tsv
    File? ko_tsv = ko_ec.ko_tsv
    File? ec_tsv = ko_ec.ec_tsv
    File? phylo_tsv = ko_ec.phylo_tsv
    File? ko_ec_gff = ko_ec.gff
    File? cog_gff = cog.gff
    File? pfam_gff = pfam.gff
    File? tigrfam_gff = tigrfam.gff
    File? supfam_gff = superfam.gff
    File? smart_gff = smart.gff
    File? cath_funfam_gff = cath_funfam.gff
    File? cog_domtblout = cog.domtblout
    File? pfam_domtblout = pfam.domtblout
    File? tigrfam_domtblout = tigrfam.domtblout
    File? supfam_domtblout = superfam.domtblout
    File? smart_domtblout = smart.domtblout
    File? cath_funfam_domtblout = cath_funfam.domtblout
  }

}

task ko_ec {

  String project_id
  String project_type
  Int    threads = 2
  File   input_fasta
  String nr_db
  String   md5
  String   phylo
  Int    top_hits = 5
  Int    min_ko_hits = 2
  Float  aln_length_ratio = 0.7
  String lastal
  String selector
  String container

  command {
    set -euo pipefail
    ${lastal} -f blasttab+ -P ${threads} ${nr_db} ${input_fasta} 1> ${project_id}_proteins.img_nr.last.blasttab
    ${selector} -l ${aln_length_ratio} -m ${min_ko_hits} -n ${top_hits} \
                ${project_type} ${md5} ${phylo} \
                ${project_id}_ko.tsv ${project_id}_ec.tsv \
                ${project_id}_gene_phylogeny.tsv ${project_id}_ko_ec.gff \
                < ${project_id}_proteins.img_nr.last.blasttab
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File last_blasttab = "${project_id}_proteins.img_nr.last.blasttab"
    File ko_tsv = "${project_id}_ko.tsv"
    File ec_tsv = "${project_id}_ec.tsv"
    File phylo_tsv = "${project_id}_gene_phylogeny.tsv"
    File gff = "${project_id}_ko_ec.gff"
  }
}

task smart {
  
  String project_id
  File   input_fasta
  String   smart_db
  Int    threads = 62
  Int    par_hmm_inst = 15
  Int    approx_num_proteins = 0
  Float  min_domain_eval_cutoff = 0.01
  Float  aln_length_ratio = 0.7
  Float  max_overlap_ratio = 0.1
  String hmmsearch
  String frag_hits_filter
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
     /opt/omics/bin/functional_annotation/hmmsearch_smart.sh ${base} \
     ${smart_db} \
     ${threads} ${par_hmm_inst} ${approx_num_proteins} \
     ${min_domain_eval_cutoff} ${aln_length_ratio} ${max_overlap_ratio} 
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_smart.gff"
    File domtblout = "${project_id}_proteins.smart.domtblout"
  }
}

task cog {
  
  String project_id
  File   input_fasta
  String   cog_db
  Int    threads = 62
  Int    par_hmm_inst = 15
  Int    approx_num_proteins = 0
  Float  min_domain_eval_cutoff = 0.01
  Float  aln_length_ratio = 0.7
  Float  max_overlap_ratio = 0.1
  String hmmsearch
  String frag_hits_filter
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
     /opt/omics/bin/functional_annotation/hmmsearch_cogs.sh ${base} \
     ${cog_db} \
     ${threads} ${par_hmm_inst} ${approx_num_proteins} \
     ${min_domain_eval_cutoff} ${aln_length_ratio} ${max_overlap_ratio} 
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_cog.gff"
    File domtblout = "${project_id}_proteins.cog.domtblout"
  }
}

task tigrfam {
  
  String project_id
  File   input_fasta
  String   tigrfam_db
  Int    threads = 62
  Int    par_hmm_inst = 15
  Int    approx_num_proteins = 0
  Float  aln_length_ratio = 0.7
  Float  max_overlap_ratio = 0.1
  String hmmsearch
  String hit_selector
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
     /opt/omics/bin/functional_annotation/hmmsearch_tigrfams.sh ${base} \
     ${tigrfam_db} \
     ${threads} ${par_hmm_inst} ${approx_num_proteins} \
     ${aln_length_ratio} ${max_overlap_ratio} 
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_tigrfam.gff"
    File domtblout = "${project_id}_proteins.tigrfam.domtblout"
  }
}

task superfam {

  String project_id
  File   input_fasta
  String   superfam_db
  Int    threads = 62
  Int    par_hmm_inst = 15
  Int    approx_num_proteins = 0
  Float  min_domain_eval_cutoff = 0.01
  Float  aln_length_ratio = 0.7
  Float  max_overlap_ratio = 0.1
  String hmmsearch
  String frag_hits_filter
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
    #Usage: hmmsearch_supfams.sh <proteins_fasta> <supfam_hmm_db> <number_of_additional_threads (default: 0)> <number_of_parallel_hmmsearch_instances (default: 0)> <approximate_number_of_total_proteins (default: 0)> <min_domain_evalue_cutoff (default 0.01)> <min_aln_length_ratio (default 0.7)> <max_overlap_ratio (default 0.1)> 

     /opt/omics/bin/functional_annotation/hmmsearch_supfams.sh ${base} \
     ${superfam_db} \
     ${threads} ${par_hmm_inst} ${approx_num_proteins} \
     ${min_domain_eval_cutoff} ${aln_length_ratio} ${max_overlap_ratio} 
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_supfam.gff"
    File domtblout = "${project_id}_proteins.supfam.domtblout"
  }
}

task pfam {

  String project_id
  File   input_fasta
  String   pfam_db
  String   pfam_claninfo_tsv
  Int    threads = 62
  Int    par_hmm_inst = 15
  Int    approx_num_proteins = 0
  String hmmsearch
  String pfam_clan_filter
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
     
    #Usage: hmmsearch_pfams.sh <proteins_fasta> <pfam_hmm_db> <pfam_claninfo_tsv> <number_of_additional_threads (default: 0)>
     /opt/omics/bin/functional_annotation/hmmsearch_pfams.sh ${base} \
     ${pfam_db} ${pfam_claninfo_tsv} \
     ${threads} ${par_hmm_inst} ${approx_num_proteins}
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_pfam.gff"
    File domtblout = "${project_id}_proteins.pfam.domtblout"
  }
}

task cath_funfam {
 
  String project_id
  File   input_fasta
  String   cath_funfam_db
  Int    threads=62
  Int    par_hmm_inst=15
  Int    approx_num_proteins=0
  Float  min_domain_eval_cutoff = 0.01
  Float  aln_length_ratio = 0.7
  Float  max_overlap_ratio = 0.1
  String hmmsearch
  String frag_hits_filter
  String base=basename(input_fasta)
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ${base}
     /opt/omics/bin/functional_annotation/hmmsearch_cath_funfams.sh  ${base} \
     ${cath_funfam_db} ${threads} ${par_hmm_inst} ${approx_num_proteins} \
     ${min_domain_eval_cutoff} ${aln_length_ratio} ${max_overlap_ratio} 
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }
  
  output {
      File gff = "${project_id}_cath_funfam.gff"
      File domtblout = "${project_id}_proteins.cath_funfam.domtblout"
  }
}

task signalp {
  
  String project_id
  File   input_fasta
  String gram_stain
  String signalp
  String container

  command <<<
    set -euo pipefail
    signalp_version=$(${signalp} -V)
    ${signalp} -t ${gram_stain} -f short ${input_fasta} | \
    grep -v '^#' | \
    awk -v sv="$signalp_version" -v ot="${gram_stain}" \
        '$10 == "Y" {print $1"\t"sv"\tcleavage_site\t"$3-1"\t"$3"\t"$2\
        "\t.\t.\tD-score="$9";network="$12";organism_type="ot}' > ${project_id}_cleavage_sites.gff
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_cleavage_sites.gff"
  }
}

task tmhmm {
  
  String project_id
  File   input_fasta
  String model
  String decode
  String decode_parser
  String container

  command <<<
    set -euo pipefail
    tool_and_version=$(${decode} -v 2>&1 | head -1)
    background="0.081 0.015 0.054 0.061 0.040 0.068 0.022 0.057 0.056 0.093 0.025"
    background="$background 0.045 0.049 0.039 0.057 0.068 0.058 0.067 0.013 0.032"
    sed 's/\*/X/g' ${input_fasta} | \
    ${decode} -N 1 -background $background -PrintNumbers \
    ${model} 2> /dev/null | ${decode_parser} "$tool_and_version" > ${project_id}_tmh.gff
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_tmh.gff"
  }
}

task product_name {
  
  String project_id
  File   sa_gff
  String product_assign
  String map_dir
  File?  ko_ec_gff
  File?  smart_gff
  File?  cog_gff
  File?  tigrfam_gff
  File?  supfam_gff
  File?  pfam_gff
  File?  cath_funfam_gff
  File?  signalp_gff
  File?  tmhmm_gff
  String container

  command {
    set -euo pipefail
    ${product_assign} ${"-k " + ko_ec_gff} ${"-s " + smart_gff} ${"-c " + cog_gff} \
                      ${"-t " + tigrfam_gff} ${"-u " + supfam_gff} ${"-p " + pfam_gff} \
                      ${"-f " + cath_funfam_gff} ${"-e " + signalp_gff} ${"-r " + tmhmm_gff} \
                      ${map_dir} ${sa_gff}
    mv ../inputs/*/*.gff .
    mv ../inputs/*/*.tsv .
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_functional_annotation.gff"
    File tsv = "${project_id}_product_names.tsv"
  }
}
