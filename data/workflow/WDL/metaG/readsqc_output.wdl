workflow readsqc_output {
    Array[File] input_files
    Array[File] stat
    Array[File] stat2
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    String proj

    call make_output {
        input: outdir=outdir,
        filtered= input_files,
        container=bbtools_container,
        proj=proj,
        stat=stat,
        stat2=stat2
    }
    call make_json_file {
        input: outdir=outdir,
        container=bbtools_container,
        stat=stat
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
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.anqdpht*}
				python <<CODE
                import json
                from collections import OrderedDict
                f = open("$i",'r')
                d = OrderedDict()
                for line in f:
                    if not line.rstrip():continue
                    key,value=line.rstrip().split('=')
                    d[key]=float(value) if 'Ratio' in key else int(value)

                with open("stat.json", 'w') as outfile:
                    json.dump(d, outfile)
                CODE
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
	String dollar ="$"
	String container
	String proj

 	command<<<
			mkdir -p ${outdir}

            for i in ${sep=' ' filtered}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.anqdpht*}
				mkdir -p ${outdir}/$prefix
                cp -f $i ${outdir}/$prefix

            done
            for i in ${sep=' ' stat}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.anqdpht*}
                cp -f $i ${outdir}/$prefix

            done
            for i in ${sep=' ' stat2}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.anqdpht*}
                cp -f $i ${outdir}/$prefix

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