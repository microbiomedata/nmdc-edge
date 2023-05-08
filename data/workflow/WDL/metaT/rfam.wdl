workflow rfam {
  String cmzscore
  String imgap_input_fasta
  String imgap_project_id
  String imgap_project_type
  Int    additional_threads
  String database_location="/refdata/database"
  String cm="${database_location}"+"Rfam/13.0/Rfam.cm"
  String claninfo_tsv="${database_location}"+"Rfam/13.0/Rfam.claninfo"
  String feature_lookup_tsv="${database_location}"+"Rfam/13.0/Rfam_feature_lookup.tsv"
  String container


  call run {
    input:
      input_fasta = imgap_input_fasta,
      project_id = imgap_project_id,
      cm = cm,
      cmzscore=cmzscore,
      feature_lookup_tsv = feature_lookup_tsv,
      claninfo_tsv = claninfo_tsv,
      threads = additional_threads,
      container=container
  }

  output {
    File misc_bind_misc_feature_regulatory_gff = run.misc_bind_misc_feature_regulatory_gff
    File rrna_gff = run.rrna_gff
    File ncrna_tmrna_gff = run.ncrna_tmrna_gff
  }
}

task run {

  String bin="/opt/omics/bin/cmsearch"
  String clan_filter_bin="/opt/omics/bin/structural_annotation/rfam_clan_filter.py"
  File   input_fasta
  String cm
  String project_id
  String cmzscore
  String claninfo_tsv
  String feature_lookup_tsv
  Int    threads
  String container

  command <<<
    set -euo pipefail
    ${bin} --notextw --cut_tc --cpu ${threads} -Z ${cmzscore} --tblout ${project_id}_rfam.tbl ${cm} ${input_fasta}
    tool_and_version=$(${bin} -h | grep INFERNAL | perl -pne 's/^.*INFERNAL/INFERNAL/' )
    grep -v '^#' ${project_id}_rfam.tbl | \
        awk '$17 == "!" {print $1,$3,$4,$6,$7,$8,$9,$10,$11,$15,$16}' | \
        sort -k1,1 -k10,10nr -k11,11n | \
        ${clan_filter_bin} "$tool_and_version" \
        ${claninfo_tsv} ${feature_lookup_tsv} > ${project_id}_rfam.gff
    awk -F'\t' '$3 == "misc_bind" || $3 == "misc_feature" || $3 == "regulatory" {print $0}' \
        ${project_id}_rfam.gff > ${project_id}_rfam_misc_bind_misc_feature_regulatory.gff
    awk -F'\t' '$3 == "rRNA" {print $0}' ${project_id}_rfam.gff > ${project_id}_rfam_rrna.gff
    awk -F'\t' '$3 == "ncRNA" || $3 == "tmRNA" {print $0}' \
        ${project_id}_rfam.gff > ${project_id}_rfam_ncrna_tmrna.gff
  >>>

  runtime {
    time: "1:00:00"
    memory: "86G"
    docker: container
  }

  output {
    File tbl = "${project_id}_rfam.tbl"
    File rfam_gff = "${project_id}_rfam.gff"
    File misc_bind_misc_feature_regulatory_gff = "${project_id}_rfam_misc_bind_misc_feature_regulatory.gff"
    File rrna_gff = "${project_id}_rfam_rrna.gff"
    File ncrna_tmrna_gff = "${project_id}_rfam_ncrna_tmrna.gff"
  }
}
