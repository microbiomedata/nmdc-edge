workflow readsqc_output {
    Array[File] input_files
    Array[File] filtered_stats_final
    Array[File] filtered_stats2_final
    Array[File] rqc_info
    Array[File] filtered_stats_json_final
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
            for i in ${sep=' ' filtered}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%_filtered.fastq.gz}
				mkdir -p ${outdir}/$prefix
                cp -f $i ${outdir}/$prefix
                cp -f $dir/$prefix_filterStats.txt ${outdir}/$prefix
                cp -f $dir/$prefix_filterStats2.txt ${outdir}/$prefix
                cp -f $dir/$prefix_qa_stats.json ${outdir}/$prefix/filterStats.json

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