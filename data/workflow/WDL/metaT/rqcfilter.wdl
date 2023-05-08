workflow jgi_rqcfilter {
    Array[File] input_files
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    String database
    Boolean chastityfilter=true
    String? memory
    String? threads

    scatter(file in input_files) {
        call rqcfilter{
             input:  input_file=file,
                     container=bbtools_container,
                     database=database,
		     chastityfilter_flag=chastityfilter,
                     memory=memory,
                     threads=threads
        }
    }

    # rqcfilter.stat implicit as Array because of scatter
    # Optional staging to an output directory
    if (defined(outdir)){
        call make_output {
           	input: outdir=outdir,
                       filtered=rqcfilter.filtered,
                       stats=rqcfilter.stat,
                       stats2=rqcfilter.stat2,
                       container=bbtools_container
        }
    }

    output{
        Array[File] filtered = rqcfilter.filtered
        Array[File] stats = rqcfilter.stat
        Array[File] stats2 = rqcfilter.stat2
        Array[File]? clean_fastq_files = make_output.fastq_files
    }
    
    parameter_meta {
        input_files: "illumina paired-end interleaved fastq files"
	outdir: "The final output directory path"
        database : "database path to RQCFilterData directory"
        clean_fastq_files: "after QC fastq files"
        memory: "optional for jvm memory for bbtools, ex: 32G"
        threads: "optional for jvm threads for bbtools ex: 16"
    }
    meta {
        author: "Chienchi Lo, B10, LANL"
        email: "chienchi@lanl.gov"
        version: "1.0.2"
    }
}

task rqcfilter {
     File input_file
     String container
     String database
     Boolean chastityfilter_flag=true
     String? memory
     String? threads
     String prefix=sub(basename(input_file), ".fastq.gz", "")
     String filename_outlog="stdout.log"
     String filename_errlog="stderr.log"
     String filename_stat="filtered/filterStats.txt"
     String filename_stat2="filtered/filterStats2.txt"
     String filename_stat_json="filtered/filterStats.json"
     String system_cpu="$(grep \"model name\" /proc/cpuinfo | wc -l)"
     String jvm_threads=select_first([threads,system_cpu])
     String chastityfilter= if (chastityfilter_flag) then "cf=t" else "cf=f"

     runtime {
            docker: container
            memory: "70 GB"
            database: database
     }

     command<<<
        #sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        set -eo pipefail
        rqcfilter2.sh -Xmx${default="60G" memory} threads=${jvm_threads} ${chastityfilter} jni=t in=${input_file} path=filtered rna=t trimfragadapter=t qtrim=r trimq=0 maxns=3 maq=3 minlen=51 mlf=0.33 phix=t removehuman=t removedog=t removecat=t removemouse=t khist=t removemicrobes=t sketch kapa=t clumpify=t tmpdir= barcodefilter=f trimpolyg=5 usejni=f rqcfilterdata=/databases/RQCFilterData  > >(tee -a ${filename_outlog}) 2> >(tee -a ${filename_errlog} >&2)

        python <<CODE
        import json
        f = open("${filename_stat}",'r')
        d = dict()
        for line in f:
            if not line.rstrip():continue
            key,value=line.rstrip().split('=')
            d[key]=float(value) if 'Ratio' in key else int(value)

        with open("${filename_stat_json}", 'w') as outfile:
            json.dump(d, outfile)
        CODE
     >>>
     output {
            File stdout = filename_outlog
            File stderr = filename_errlog
            File stat = filename_stat
            File stat2 = filename_stat2
            File filtered = glob("filtered/*fastq.gz")[0]
            File json_out = filename_stat_json
     }
}

task make_output{
 	String outdir
	Array[File] stats
	Array[File] stats2
	Array[File] filtered
	String container
 
 	command<<<
			mkdir -p ${outdir}
			for i in ${sep=' ' stats}
			do
				cp -f $i ${outdir}
			done
			for i in ${sep=' ' stats2}
			do
				cp -f $i ${outdir}
			done
			for i in ${sep=' ' filtered}
			do
				cp -f $i ${outdir}
			done
 			chmod 764 -R ${outdir}
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
		Array[String] fastq_files = glob("${outdir}/*.fastq*")
	}
}

