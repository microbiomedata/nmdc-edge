workflow annotation_output {
  String  imgap_project_type="metagenome"
  String  container="bfoster1/img-omics:0.1.9"
  String? outdir
  File final_stats_tsv
  File functional_gff


  call make_output {
      input:
        OUTPATH = outdir,
        stats = final_stats_tsv,
        gff = functional_gff,
        projectName = imgap_project_type,
        container = container
  }
}
task make_output {
    String OUTPATH
    String stats
    String gff
    String projectName
    String container

    command <<<
        echo ${OUTPATH}

        mkdir -p ${OUTPATH}
		Statspath=`dirname ${stats}`
        echo $Statspath
		GFFPath=`dirname ${gff}`
        echo $GFFPath
		cp $Statspath/* ${OUTPATH}/
		cp ${OUTPATH}/${projectName}_stats.json ${OUTPATH}/${projectName}_structural_annotation_stats.json
		cp $GFFPath/* ${OUTPATH}/
        ls ${OUTPATH}
		chmod 764 -R ${OUTPATH}
    >>>

    runtime{
        mem: "1GB"
        cpu: 1
        docker: container
    }
}
