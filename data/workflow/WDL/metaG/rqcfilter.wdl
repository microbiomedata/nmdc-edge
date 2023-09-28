workflow jgi_rqcfilter {
    Array[File] input_files
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    String database="/refdata"
    Boolean chastityfilter=false
    String? memory
    String? threads
    Boolean input_interleaved = true
    Array[File] input_fq1
    Array[File] input_fq2
    
    if (!input_interleaved) {
        ## the zip() function generates an array of pairs, use .left and .right to access
        scatter(file in zip(input_fq1,input_fq2)){
             call interleave_reads {
                 input:
                     input_files = [file.left,file.right],
                     output_file = basename(file.left) + "_" + basename(file.right),
	             container = bbtools_container
             }
             call rqcfilter as rqcPE {
                 input:  input_file=interleave_reads.out_fastq,
                     container=bbtools_container,
                     database=database,
                     chastityfilter_flag=chastityfilter,
                     memory=memory,
                     threads=threads
	
            }
        }
    }

    if (input_interleaved) {
        scatter(file in input_files) {
            call rqcfilter as rqcInt {
                 input:  input_file=file,
                     container=bbtools_container,
                     database=database,
		     chastityfilter_flag=chastityfilter,
                     memory=memory,
                     threads=threads
            }
        }
    }

    # rqcfilter.stat implicit as Array because of scatter
    # Optional staging to an output directory
    if (defined(outdir)){

        call make_output {
           	input: outdir=outdir,
                       filtered= if (input_interleaved) then rqcInt.filtered else rqcPE.filtered,
                       container=bbtools_container
        }
    }

    output{
        Array[File]? filtered = if (input_interleaved) then rqcInt.filtered else rqcPE.filtered
        Array[File]? stats = if (input_interleaved) then rqcInt.stat else rqcPE.stat
        Array[File]? stats2 = if (input_interleaved) then rqcInt.stat2 else rqcPE.stat2
        Array[File]? statsjson = if (input_interleaved) then rqcInt.json_out else rqcPE.json_out
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
     String prefix=sub(basename(input_file), ".fa?s?t?q.?g?z?$", "")
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

        rqcfilter2.sh -Xmx${default="60G" memory} threads=${jvm_threads} ${chastityfilter} jni=t in=${input_file} path=filtered rna=f trimfragadapter=t qtrim=r trimq=0 maxns=3 maq=3 minlen=51 mlf=0.33 phix=t removehuman=t removedog=t removecat=t removemouse=t khist=t removemicrobes=t sketch kapa=t clumpify=t tmpdir= barcodefilter=f trimpolyg=5 usejni=f rqcfilterdata=${database}/RQCFilterData  > >(tee -a ${filename_outlog}) 2> >(tee -a ${filename_errlog} >&2)

        python <<CODE
        import json
        from collections import OrderedDict
        f = open("${filename_stat}",'r')
        d = OrderedDict()
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
            File filtered = glob("filtered/*anqdpht*")[0]
            File json_out = filename_stat_json
     }
}

task make_output{
 	String outdir
	Array[String] filtered
	String dollar ="$"
	String container
 
 	command<<<
			mkdir -p ${outdir}
			for i in ${sep=' ' filtered}
			do
				f=${dollar}(basename $i)
				dir=${dollar}(dirname $i)
				prefix=${dollar}{f%.anqdpht*}
				mkdir -p ${outdir}/$prefix
				cp -f $dir/../filtered/filterStats.txt ${outdir}/$prefix
				cp -f $dir/../filtered/filterStats2.txt ${outdir}/$prefix
				cp -f $dir/../filtered/filterStats.json ${outdir}/$prefix
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

task interleave_reads{

        Array[File] input_files
        String output_file = "interleaved.fastq.gz"
	String container
        
        command <<<
            if file --mime -b ${input_files[0]} | grep gzip > /dev/null ; then 
                paste <(gunzip -c ${input_files[0]} | paste - - - -) <(gunzip -c ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}
		echo ${output_file}
            else
                if [[ "${output_file}" == *.gz ]]; then
                    paste <(cat ${input_files[0]} | paste - - - -) <(cat ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}
		    echo ${output_file}
                else
                    paste <(cat ${input_files[0]} | paste - - - -) <(cat ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}.gz
                    echo ${output_file}.gz
                fi
            fi
        >>>
        
        runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
        
        output {
                File out_fastq = read_string(stdout())
        }
}
