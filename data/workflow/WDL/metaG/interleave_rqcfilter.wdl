workflow nmdc_rqcfilter {
    String  container="bfoster1/img-omics:0.1.9"
    String  bbtools_container="microbiomedata/bbtools:38.96"
    String  proj
    String  input_fastq1
    String  input_fastq2
    String  database="/refdata/"

    call stage {
        input: container=bbtools_container,
            memory="10G",
            input_fastq1=input_fastq1,
            input_fastq2=input_fastq2
    }
    # Estimate RQC runtime at an hour per compress GB
    call rqcfilter as qc {
        input: input_files=stage.interleaved_reads,
            threads=16,
            database=database,
            memory="60G"
    }
    call make_info_file {
        input: info_file = qc.info_file,
            container=container,
            proj=proj
    }

    call finish_rqc {
        input: container="microbiomedata/workflowmeta:1.1.1",
           proj=proj,
           start=stage.start,
           read = stage.interleaved_reads,
           filtered = qc.filtered,
           filtered_stats = qc.stat,
           filtered_stats2 = qc.stat2
    }
    output {
        File filtered_final = finish_rqc.filtered_final
        File filtered_stats_final = finish_rqc.filtered_stats_final
        File filtered_stats2_final = finish_rqc.filtered_stats2_final
        File rqc_info = make_info_file.rqc_info
    }
}



task stage {
   String container
   String memory
   String target_reads_1="raw_reads_1.fastq.gz"
   String target_reads_2="raw_reads_2.fastq.gz"
   String output_interleaved="raw_interleaved.fastq.gz"
   String input_fastq1
   String input_fastq2

   command <<<
       set -e
       if [ $( echo ${input_fastq1} | egrep -c "https*:") -gt 0 ] ; then
           wget ${input_fastq1} -O ${target_reads_1}
           wget ${input_fastq2} -O ${target_reads_2}
       else
           ln ${input_fastq1} ${target_reads_1} || cp ${input_fastq1} ${target_reads_1}
           ln ${input_fastq2} ${target_reads_2} || cp ${input_fastq2} ${target_reads_2}
       fi

       reformat.sh -Xmx${memory} in1=${target_reads_1} in2=${target_reads_2} out=${output_interleaved}
       # Capture the start time
       date --iso-8601=seconds > start.txt

   >>>

   output{
      File interleaved_reads = "${output_interleaved}"
      String start = read_string("start.txt")
   }
   runtime {
     memory: "1 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }
}


task rqcfilter {
     File input_files
     String container="microbiomedata/bbtools:38.96"
     String database
     Boolean chastityfilter_flag=true
     String? memory
     String? threads
     String filename_outlog="stdout.log"
     String filename_errlog="stderr.log"
     String filename_stat="filtered/filterStats.txt"
     String filename_stat2="filtered/filterStats2.txt"
     String filename_stat_json="filtered/filterStats.json"
     String filename_reproduce="filtered/reproduce.sh"
     String system_cpu="$(grep \"model name\" /proc/cpuinfo | wc -l)"
     String jvm_threads=select_first([threads,system_cpu])
     String chastityfilter= if (chastityfilter_flag) then "cf=t" else "cf=f"

     runtime {
            docker: container
            memory: "70 GB"
            cpu:  16
            database: database
            runtime_minutes: ceil(size(input_files, "GB")*60)
     }

     command<<<
        #sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        set -eo pipefail
        rqcfilter2.sh -Xmx${default="60G" memory} -da threads=${jvm_threads} ${chastityfilter} jni=t in=${input_files} path=filtered rna=f trimfragadapter=t qtrim=r trimq=0 maxns=3 maq=3 minlen=51 mlf=0.33 phix=t removehuman=t removedog=t removecat=t removemouse=t khist=t removemicrobes=t sketch kapa=t clumpify=t tmpdir= barcodefilter=f trimpolyg=5 usejni=f rqcfilterdata=${database}/RQCFilterData  > >(tee -a ${filename_outlog}) 2> >(tee -a ${filename_errlog} >&2)

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
            File info_file = filename_reproduce
            File filtered = glob("filtered/*fastq.gz")[0]
            File json_out = filename_stat_json
            #String start = read_string("start.txt")
     }
}

task make_info_file {
    File info_file
    String proj
    String prefix=sub(proj, ":", "_")
    String container
    
    command<<<
        sed -n 2,5p ${info_file} 2>&1 |  perl -ne 's:in=/.*/(.*) :in=$1:; s/#//; s/BBTools/BBTools(1)/; print;' > ${prefix}_readsQC.info
        echo -e "\n(1) B. Bushnell: BBTools software package, http://bbtools.jgi.doe.gov/" >> ${prefix}_readsQC.info
    >>>

    output {
        File rqc_info = "${prefix}_readsQC.info"
    }
    runtime {
        memory: "1 GiB"
        cpu:  1
        maxRetries: 1
        docker: container
    }
}

task finish_rqc {
    File read
    File filtered_stats
    File filtered_stats2
    File filtered
    String container
    String proj
    String prefix=sub(proj, ":", "_")
    String start
 
    command<<<

        set -e
        end=`date --iso-8601=seconds`
        # Generate QA objects
        ln ${filtered} ${prefix}_filtered.fastq.gz
        ln ${filtered_stats} ${prefix}_filterStats.txt
        ln ${filtered_stats2} ${prefix}_filterStats2.txt

       # Generate stats but rename some fields untilt the script is
       # fixed.
       /scripts/rqcstats.py ${filtered_stats} > stats.json
       cp stats.json ${prefix}_qa_stats.json

    >>>
    output {
        File filtered_final = "${prefix}_filtered.fastq.gz"
        File filtered_stats_final = "${prefix}_filterStats.txt"
        File filtered_stats2_final = "${prefix}_filterStats2.txt"
    }

    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
}
