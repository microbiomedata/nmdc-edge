workflow readsqc_output {
    File input_files
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
	String filtered
	String dollar ="$"
	String container

 	command<<<
			mkdir -p ${outdir}

            f=${dollar}(basename $filtered)
            dir=${dollar}(dirname $filtered)
            prefix=${dollar}{f%.anqdpht*}
            mkdir -p ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats.txt ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats2.txt ${outdir}/$prefix
            cp -f $dir/../filtered/filterStats.json ${outdir}/$prefix
            cp -f $i ${outdir}/$prefix
            echo ${outdir}/$prefix/$f

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