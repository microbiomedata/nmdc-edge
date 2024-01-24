workflow readsqc_output {
    Array[File] input_files
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"

    call make_output {
        input: outdir=outdir,
        filtered= input_files,
        container=bbtools_container
    }
}

task make_output{
 	String outdir
	Array[File] filtered
	String dollar ="$"
	String container

 	command<<<
			mkdir -p ${outdir}

            mkdir -p ${outdir}/$prefix
            cp -f glob("*fastq.gz") ${outdir}
            cp -f ${prefix}_filterStats.txt ${outdir}/$prefix
            cp -f ${prefix}_filterStats2.txt ${outdir}/$prefix
            cp -f ${prefix}_filterStats.json ${outdir}/$prefix


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