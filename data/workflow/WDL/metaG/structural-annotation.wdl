import "trnascan.wdl" as trnascan
import "rfam.wdl" as rfam
import "crt.wdl" as crt
import "cds_prediction.wdl" as cds_prediction

workflow s_annotate {
  String  cmzscore
  File    imgap_input_fasta
  String  imgap_project_id
  String  imgap_project_type
  Int     additional_threads
  Int? imgap_structural_annotation_translation_table
  Boolean pre_qc_execute=false
  Boolean trnascan_se_execute=true
  Boolean rfam_execute=true
  Boolean crt_execute=true
  Boolean cds_prediction_execute=true
  Boolean prodigal_execute=true
  Boolean genemark_execute=true
  Boolean gff_and_fasta_stats_execute=true
  String  database_location
  String  container
  String? gm_license

  if(pre_qc_execute) {
    call pre_qc {
      input:
        project_type = imgap_project_type,
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        container=container
    }
  }
  if(trnascan_se_execute) {
    call trnascan.trnascan {
      input:
        imgap_input_fasta = imgap_input_fasta,
        imgap_project_id = imgap_project_id,
        imgap_project_type = imgap_project_type,
        additional_threads = additional_threads,
        container=container
    }
  }
  if(rfam_execute) {
    call rfam.rfam {
      input:
        cmzscore = cmzscore,
        imgap_input_fasta = imgap_input_fasta,
        imgap_project_id = imgap_project_id,
        imgap_project_type = imgap_project_type,
        database_location = database_location,
        additional_threads = additional_threads,
        container=container
    }
  }
  if(crt_execute) {
    call crt.crt {
      input:
        imgap_input_fasta = imgap_input_fasta,
        imgap_project_id = imgap_project_id,
        container=container
    }
  }

   if(cds_prediction_execute) {
     call cds_prediction.cds_prediction {
       input:
         imgap_input_fasta = imgap_input_fasta,
         imgap_project_id = imgap_project_id,
         imgap_project_type = imgap_project_type,
         prodigal_execute = prodigal_execute,
         genemark_execute = genemark_execute,
         imgap_structural_annotation_translation_table = imgap_structural_annotation_translation_table,
         container = container,
         gm_license = gm_license
    }
  }


    call gff_merge {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        rfam_gff = rfam.rfam_gff,
        trna_gff = trnascan.gff,
        crt_gff = crt.gff, 
        cds_gff = cds_prediction.gff,
        prodigal_execute = prodigal_execute,
        genemark_execute = genemark_execute,
        crt_execute = crt_execute,
        rfam_execute = rfam_execute,
        trnascan_se_execute = trnascan_se_execute,
        container = container
    }

  if(prodigal_execute || genemark_execute)  {
    call fasta_merge {
      input:
       # input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        final_gff = gff_merge.final_gff,
        cds_genes = cds_prediction.genes,
        cds_proteins = cds_prediction.proteins,
        container = container
    }
  }

  if(gff_and_fasta_stats_execute) {
    call gff_and_fasta_stats {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        final_gff = gff_merge.final_gff,
        container = container
    }
  }
  if(imgap_project_type == "isolate") {
    call post_qc {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        container = container
    }
  }
  output {
    File  gff = gff_merge.final_gff 
    File? crt_gff = crt.gff
    File? crisprs = crt.crisprs 
    File? crt_out = crt.crt_out
    File? genemark_gff = cds_prediction.genemark_gff
    File? genemark_genes = cds_prediction.genemark_genes
    File? genemark_proteins = cds_prediction.genemark_proteins 
    File? prodigal_gff = cds_prediction.prodigal_gff
    File? prodigal_genes = cds_prediction.prodigal_genes
    File? prodigal_proteins = cds_prediction.prodigal_proteins
    File? cds_gff = cds_prediction.gff
    File? cds_proteins = cds_prediction.proteins
    File? cds_genes = cds_prediction.genes
    File? trna_gff = trnascan.gff
    File? trna_bacterial_out = trnascan.bacterial_out
    File? trna_archaeal_out = trnascan.archaeal_out
    File? rfam_gff = rfam.rfam_gff
    File? rfam_tbl = rfam.rfam_tbl
    String? rfam_version = rfam.rfam_version
    File? proteins = fasta_merge.final_proteins
    File? genes = fasta_merge.final_genes
  }
}

task pre_qc {
  String bin="/opt/omics/bin/qc/pre-annotation/fasta_sanity.py"
  String project_type
  File   input_fasta
  String project_id
  String rename = "yes"
  Float  n_ratio_cutoff = 0.5
  Int    seqs_per_million_bp_cutoff = 500
  Int    min_seq_length = 150
  String container

  command <<<
    set -euo pipefail
    tmp_fasta="${input_fasta}.tmp"
    qced_fasta="${project_id}_contigs.fna"
    grep -v '^\s*$' ${input_fasta} | tr -d '\r' | \
    sed 's/^>[[:blank:]]*/>/g' > $tmp_fasta
    acgt_count=`grep -v '^>' $tmp_fasta | grep -o [acgtACGT] | wc -l`
    n_count=`grep -v '^>' $tmp_fasta | grep -o '[^acgtACGT]' | wc -l`
    n_ratio=`echo $n_count $acgt_count | awk '{printf "%f", $1 / $2}'`
    if (( $(echo "$n_ratio >= ${n_ratio_cutoff}" | bc) ))
    then
        rm $tmp_fasta
        exit 1
    fi

    if [[ ${project_type} == "isolate" ]]
    then
        seq_count=`grep -c '^>' $tmp_fasta`
        bp_count=`grep -v '^>' $tmp_fasta | tr -d '\n' | wc -m`
        seqs_per_million_bp=$seq_count
        if (( $bp_count > 1000000 ))
        then
            divisor=$(echo $bp_count | awk '{printf "%.f", $1 / 1000000}')
            seqs_per_million_bp=$(echo $seq_count $divisor | \
                                  awk '{printf "%.2f", $1 / $2}')
        fi
        if (( $(echo "$seqs_per_million_bp > ${seqs_per_million_bp_cutoff}" | bc) ))
        then
            rm $tmp_fasta
            exit 1
        fi
    fi

    fasta_sanity_cmd="${bin} $tmp_fasta $qced_fasta"
    if [[ ${rename} == "yes" ]]
    then
        fasta_sanity_cmd="$fasta_sanity_cmd -p ${project_id}"
    fi
    fasta_sanity_cmd="$fasta_sanity_cmd -l ${min_seq_length}"
    $fasta_sanity_cmd
    rm $tmp_fasta
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }
    
  output {
    File fasta = "${project_id}_contigs.fna"
  }
}

task gff_merge {

  String bin="/opt/omics/bin/structural_annotation/gff_files_merger.py"
  File   input_fasta
  String project_id
  File?  rrna_gff
  File?  trna_gff
  File?  rfam_gff
  File?  crt_gff
  File?  cds_gff 
  Boolean prodigal_execute
  Boolean genemark_execute
  Boolean crt_execute
  Boolean rfam_execute
  Boolean trnascan_se_execute
  String container
  command {
    set -euo pipefail
    # set cromwell booleans as bash variables
    prodigal_execute=${prodigal_execute}  
    genemark_execute=${genemark_execute}
    crt_execute=${crt_execute}
    rfam_execute=${rfam_execute}
    trnascan_se_execute=${trnascan_se_execute}

    #construct arguments for gff_files_merger.py
    merger_args="--contigs_fasta ${input_fasta}"

    if [[ "$prodigal_execute" = true ]] || [[ "$genemark_execute" = true ]] ; then
       merger_args="$merger_args --cds_gff ${cds_gff}"
    fi

    if [[ "$crt_execute" = true ]] ; then
       merger_args="$merger_args --crt_gff ${crt_gff}"
    fi

    if [[ ("$prodigal_execute" = true || "$genemark_execute" = true) ]] && [[ "$crt_execute" = true ]] ; then
       merger_args="$merger_args --log_file ${project_id}_gff_merge.log"
    fi

    if [[ "$rfam_execute" = true ]] ; then
       merger_args="$merger_args ${rfam_gff}"
    fi

    if [[ "$trnascan_se_execute" = true ]] ; then
       merger_args="$merger_args ${trna_gff}"
    fi

    #excute gff_files_merger.py
    ${bin} $merger_args 1> ${project_id}_structural_annotation.gff


  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File final_gff = "${project_id}_structural_annotation.gff"
  }
}

task fasta_merge {

  String bin="/opt/omics/bin/structural_annotation/finalize_fasta_files.py"
  String project_id
  File   final_gff
  File cds_genes
  File cds_proteins
  String genes_filename = basename(cds_genes)
  String proteins_filename = basename(cds_proteins)
  String container

  command {
   set -euo pipefail
   cp ${final_gff} .
   cp ${cds_genes} .
   cp ${cds_proteins} .
   ${bin} ${final_gff} ${genes_filename} ${proteins_filename}
  }

  runtime {
    time: "2:00:00"
    memory: "40G"
    docker: container
  }
    
  output {
    File final_genes = "${project_id}_genes.fna"
    File final_proteins = "${project_id}_proteins.faa"
  }
}

task gff_and_fasta_stats {

  String bin="/opt/omics/bin/structural_annotation/gff_and_final_fasta_stats.py"
  File   input_fasta
  String project_id
  File   final_gff
  String container

  command {
    ${bin} ${input_fasta} ${final_gff}
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }
    
}

task post_qc {

  String qc_bin="/opt/omics/bin/qc/post-annotation/genome_structural_annotation_sanity.py"
  File   input_fasta
  String project_id
  String container

  command {
    ${qc_bin} ${input_fasta} "${project_id}_structural_annotation.gff"
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }
    
  output {
    File out = "${project_id}_structural_annotation.gff"
  }
}
