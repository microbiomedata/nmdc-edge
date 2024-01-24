workflow readsqc_output {
    Array[File] input_files
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    String proj

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
	String proj

 	command<<<
			mkdir -p ${outdir}

            mkdir -p ${outdir}/$proj
            cp -f glob("*fastq.gz") ${outdir}
            cp -f ${proj}_filterStats.txt ${outdir}/$proj
            cp -f ${proj}_filterStats2.txt ${outdir}/$proj
            cp -f ${proj}_filterStats.json ${outdir}/$proj


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