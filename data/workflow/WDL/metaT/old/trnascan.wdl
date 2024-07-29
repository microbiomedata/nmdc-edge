workflow trnascan {

  String imgap_input_fasta
  String imgap_project_id
  String imgap_project_type
  Int    additional_threads
  String container

  call trnascan_ba {
    input:
      input_fasta = imgap_input_fasta,
      project_id = imgap_project_id,
      threads = additional_threads,
      container=container
  }
  output {
    File gff = trnascan_ba.gff
  }
  meta {
     author: "Brian Foster"
     email: "bfoster@lbl.gov"
     version: "1.0.0"
  }
}

task trnascan_ba {

  String bin="/opt/omics/bin/tRNAscan-SE"
  File input_fasta
  String project_id
  Int    threads
  String container

  command <<<
     set -euo pipefail
     cp ${input_fasta} ./${project_id}_contigs.fna
     /opt/omics/bin/structural_annotation/trnascan-se_trnas.sh ${project_id}_contigs.fna metagenome ${threads}
  >>>

  runtime {
    time: "9:00:00"
    docker: "scanon/im-trnascan:v0.0.1"
    shared: "1"
    memory: "115G"
    poolname: "tuesday-one"
    node: 5
    nwpn: 8
  }

  output {
    File bacterial_out = "${project_id}_trnascan_bacterial.out"
    File archaeal_out  = "${project_id}_trnascan_archaeal.out"
    File gff = "${project_id}_trna.gff"
  }
}
