workflow readsqc_output {
    Array[File] input_files
    Array[File] stat
    Array[File] stat2
    Array[File] stat_json
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    String proj

    call make_output {
        input: outdir=outdir,
        filtered= input_files,
        container=bbtools_container,
        proj=proj,
        stat=stat,
        stat2=stat2,
        stat_json=stat_json
    }

}

task make_json_file {
    String outdir
    Array[File] stat
    String container
	String dollar ="$"
    command<<<
        for i in ${sep=' ' stat}
	    do
            python <<CODE
            print("hello world")
            CODE
        done
	>>>
	runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
	output{
		Array[String] fastq_files = read_lines(stdout())
	}

}
task make_output{
 	String outdir
	Array[File] filtered
	Array[File] stat
	Array[File] stat2
	Array[File] stat_json
	String dollar ="$"
	String container
	String proj

 	command<<<
			mkdir -p ${outdir}

            for i in ${sep=' ' filtered}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.fastq*}
				mkdir -p ${outdir}/$prefix
                cp -f ${outdir}/filterStats.txt ${outdir}/$prefix
				cp -f ${outdir}/filterStats2.txt ${outdir}/$prefix
				cp -f ${outdir}/filterStats.json ${outdir}/$prefix
				cp -f $i ${outdir}/$prefix
                echo ${outdir}/$prefix/$f
            done




 			chmod 764 -R ${outdir}
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
		Array[String] fastq_files = read_lines(stdout())
	}
}