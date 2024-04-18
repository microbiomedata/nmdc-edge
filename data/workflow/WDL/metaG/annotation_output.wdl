workflow annotation_output {
    String  imgap_project_type="metagenome"
    String  container="bfoster1/img-omics:0.1.9"
    String  vis_container="microbiomedata/annotation_vis:0.1.0"
    String  opaver_web_path
    String? outdir
    File final_stats_tsv
    File functional_gff

    call annotation_vis {
        input:
        container= vis_container,
        gff = functional_gff,
        projectName = imgap_project_type,
        opaver_web_path = opaver_web_path,
        OUTPATH = outdir
    }

    call make_output {
        input:
        OUTPATH = outdir,
        stats = final_stats_tsv,
        gff = functional_gff,
        projectName = imgap_project_type,
        container = container
    }
}

task annotation_vis{
    String OUTPATH
    String PROJPATH=sub(OUTPATH, "output/MetagenomeAnnotation", "")
    String opaver_web_path
    File gff
    String projectName
    String container

    command <<<
	cp /opt/conda/envs/annotationVis/bin/opaver_anno.pl .
	cp -r /opt/conda/envs/annotationVis/bin/ec_info ec_info
        perl opaver_anno.pl -g ${gff}  -o ${OUTPATH}/kegg_map
        ## make symlink to omics-pathway-viewer/data location
        projectID=`basename ${PROJPATH}`
        ln -s ${OUTPATH}/kegg_map ${opaver_web_path}/$projectID

        plot_protein_len.py --input ${gff} --output ${OUTPATH}/${projectName}.protein_size_histogram.html
	chmod -R 755 ${OUTPATH}
    >>>

    output {
        File protein_size_hist = "${OUTPATH}/${projectName}.protein_size_histogram.html"
    }

    runtime{
        mem:"1GB"
        cpu: 1
        docker: container
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
