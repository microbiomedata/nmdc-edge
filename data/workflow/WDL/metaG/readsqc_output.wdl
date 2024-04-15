workflow readsqc_output {
    File input_file
    File stat
    File stat2
    File stat_json
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
	File filtered
	File stat
	File stat2
	File stat_json
	String dollar ="$"
	String container
	String proj

 	command<<<
			mkdir -p ${outdir}
			f=${dollar}(basename $i)
			dir=${dollar}(dirname $i)
			prefix=${dollar}{f%.fastq*}
            cp ${filtered} ${outdir}/$prefix
            cp ${stat} ${outdir}/$prefix
			cp ${stat2} ${outdir}/$prefix
			cp ${stat_json} ${outdir}/$prefix

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