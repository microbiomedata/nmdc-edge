import "trnascan.wdl" as trnascan
import "rfam.wdl" as rfam
import "crt.wdl" as crt
import "prodigal.wdl" as prodigal
import "genemark.wdl" as genemark

workflow s_annotate {
  String  cmzscore
  File    imgap_input_fasta
  String  imgap_project_id
  String  imgap_project_type
  Int     additional_threads
  Boolean pre_qc_execute=false
  Boolean trnascan_se_execute=true
  Boolean rfam_execute=true
  Boolean crt_execute=true
  Boolean prodigal_execute=true
  Boolean genemark_execute=true
  Boolean gff_and_fasta_stats_execute=true
  String  database_location
  String  container

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
  if(prodigal_execute) {
    call prodigal.prodigal {
      input:
        imgap_input_fasta = imgap_input_fasta,
        imgap_project_id = imgap_project_id,
        imgap_project_type = imgap_project_type,
        container=container
    }
  }
  if(genemark_execute) {
    call genemark.genemark {
      input:
        imgap_input_fasta = imgap_input_fasta,
        imgap_project_id = imgap_project_id,
        imgap_project_type = imgap_project_type,
        container=container
    }
  }
  call gff_merge {
    input:
      input_fasta = imgap_input_fasta,
      project_id = imgap_project_id,
      misc_and_regulatory_gff = rfam.misc_bind_misc_feature_regulatory_gff,
      rrna_gff = rfam.rrna_gff,
      trna_gff = trnascan.gff,
      ncrna_tmrna_gff = rfam.ncrna_tmrna_gff,
      crt_gff = crt.gff, 
      genemark_gff = genemark.gff,
      prodigal_gff = prodigal.gff,
      container=container
  }
  if(prodigal_execute || genemark_execute) {
    call fasta_merge {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        final_gff = gff_merge.final_gff,
        genemark_genes = genemark.genes,
        genemark_proteins = genemark.proteins,
        prodigal_genes = prodigal.genes,
        prodigal_proteins = prodigal.proteins,
        container=container
    }
  }
  if(gff_and_fasta_stats_execute) {
    call gff_and_fasta_stats {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        final_gff = gff_merge.final_gff,
        container=container
    }
  }
  if(imgap_project_type == "isolate") {
    call post_qc {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        container=container
    }
  }
  output {
    #File  gff = gff_merge.final_gff
    #File  gff = post_qc.out
    File?  gff = fasta_merge.final_modified_gff
    File? crt_gff = crt.gff
    File? crisprs = crt.crisprs 
    File? genemark_gff = genemark.gff
    File? prodigal_gff = prodigal.gff
    File? trna_gff = trnascan.gff
    File? misc_bind_misc_feature_regulatory_gff = rfam.misc_bind_misc_feature_regulatory_gff
    File? rrna_gff = rfam.rrna_gff
    File? ncrna_tmrna_gff = rfam.ncrna_tmrna_gff
    File? proteins = fasta_merge.final_proteins 
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
  File?  misc_and_regulatory_gff
  File?  rrna_gff
  File?  trna_gff
  File?  ncrna_tmrna_gff
  File?  crt_gff
  File?  genemark_gff
  File?  prodigal_gff
  String container

  command {
    set -euo pipefail
    ${bin} -f ${input_fasta} ${"-a " + misc_and_regulatory_gff + " " + rrna_gff} \
    ${trna_gff} ${ncrna_tmrna_gff} ${crt_gff} \
    ${genemark_gff} ${prodigal_gff} 1> ${project_id}_structural_annotation.gff
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

  String bin="/opt/omics/bin/structural_annotation/fasta_files_merger.py"
  File   input_fasta
  String project_id
  File   final_gff
  File?  genemark_genes
  File?  genemark_proteins
  File?  prodigal_genes
  File?  prodigal_proteins
  String final_gff_out=basename(final_gff)
  String container

  command {
    set -euo pipefail
    cp ${final_gff} ${final_gff_out}
    ${bin} ${final_gff_out} ${genemark_genes} ${prodigal_genes} 1> ${project_id}_genes.fna
    ${bin} ${final_gff_out} ${genemark_proteins} ${prodigal_proteins} 1> ${project_id}_proteins.faa
  }

  runtime {
    time: "2:00:00"
    memory: "40G"
    docker: "doejgi/img-annotation-pipeline:5.0.25"
  }
    
  output {
    File final_genes = "${project_id}_genes.fna"
    File final_proteins = "${project_id}_proteins.faa"
    File final_modified_gff = "${final_gff_out}"
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
