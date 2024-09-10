workflow genemark {
  
  String imgap_input_fasta
  String imgap_project_id
  String imgap_project_type
  String container

  if(imgap_project_type == "isolate") {
    call gm_isolate {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        container=container
    }
  }
  if(imgap_project_type == "metagenome") {
    call gm_meta {
      input:
        input_fasta = imgap_input_fasta,
        project_id = imgap_project_id,
        container=container
    }
  }
  call clean_and_unify {
    input:
      iso_genes_fasta = gm_isolate.genes,
      meta_genes_fasta = gm_meta.genes,
      iso_proteins_fasta = gm_isolate.proteins,
      meta_proteins_fasta = gm_meta.proteins,
      iso_gff = gm_isolate.gff,
      meta_gff = gm_meta.gff,
      project_id = imgap_project_id,
      container=container
  }

  output {
    File gff = clean_and_unify.gff
    File genes = clean_and_unify.genes
    File proteins = clean_and_unify.proteins
  }
}

task gm_isolate {
  
  String bin="/opt/omics/bin/gms2.pl"
  File   input_fasta
  String project_id
  String container

  command {
    set -euo pipefail
    ${bin} --seq ${input_fasta} --genome-type auto \
           --output ${project_id}_genemark.gff --format gff \
           --fnn ${project_id}_genemark_genes.fna \
           --faa ${project_id}_genemark_proteins.faa
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_genemark.gff"
    File genes = "${project_id}_genemark_genes.fna"
    File proteins = "${project_id}_genemark_proteins.faa"
  }
}

task gm_meta {
  
  String bin="/opt/omics/bin/gmhmmp2"

  String model="/opt/omics/programs/GeneMark/GeneMarkS-2/v1.07/mgm_11.mod"
  File   input_fasta
  String project_id
  String container

  command {
    set -euo pipefail
    ${bin} --Meta ${model} --incomplete_at_gaps 30 \
           -o ${project_id}_genemark.gff \
           --format gff --NT ${project_id}_genemark_genes.fna \
           --AA ${project_id}_genemark_proteins.faa --seq ${input_fasta}
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_genemark.gff"
    File genes = "${project_id}_genemark_genes.fna"
    File proteins = "${project_id}_genemark_proteins.faa"
  }
}

task clean_and_unify {
  File?  iso_genes_fasta
  File?  meta_genes_fasta
  File?  iso_proteins_fasta
  File?  meta_proteins_fasta
  File?  iso_gff
  File?  meta_gff
  String unify_bin="/opt/omics/bin/structural_annotation/unify_gene_ids.py"
  String project_id
  String container
  
  command {
    set -uo pipefail
    sed -i 's/\*/X/g' ${iso_proteins_fasta} ${meta_proteins_fasta}
    ${unify_bin} ${iso_gff} ${meta_gff} \
                 ${iso_genes_fasta} ${meta_genes_fasta} \
                 ${iso_proteins_fasta} ${meta_proteins_fasta}
    mv ${iso_proteins_fasta} . 2> /dev/null
    mv ${meta_proteins_fasta} . 2> /dev/null
    mv ${iso_genes_fasta} . 2> /dev/null
    mv ${meta_genes_fasta} . 2> /dev/null
    mv ${iso_gff} . 2> /dev/null
    mv ${meta_gff} . 2> /dev/null
  }

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File gff = "${project_id}_genemark.gff"
    File genes = "${project_id}_genemark_genes.fna"
    File proteins = "${project_id}_genemark_proteins.faa"
  }
}

