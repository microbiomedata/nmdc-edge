workflow nmdc_rqcfilter {
    String  container="bfoster1/img-omics:0.1.9"
    String  proj
    String  input_files
    String  database="/refdata/img/"
    String  resource
    String  informed_by
    String?  git_url="https://github.com/microbiomedata/mg_annotation/releases/tag/0.1"
    String?  url_root="https://data.microbiomedata.org/data/"
    String  url_base="${url_root}${proj}/qa/"

    call stage {
        input: container=container,
            input_file=input_files
    }
    # Estimate RQC runtime at an hour per compress GB
    call rqcfilter as qc {
        input: input_files=stage.read,
            threads=16,
            database=database,
            memory="60G"
    }

    call finish_rqc {
        input: container="microbiomedata/workflowmeta:1.1.0",
           proj=proj,
           start=stage.start,
           resource=resource,
           url_root=url_root,
           git_url=git_url,
           informed_by=informed_by,
           read = stage.read,
           filtered = qc.filtered,
           filtered_stats = qc.stat,
           filtered_stats2 = qc.stat2
    }
    output {
        File filtered_final = finish_rqc.filtered_final
        File filtered_stats_final = finish_rqc.filtered_stats_final
        File filtered_stats2_final = finish_rqc.filtered_stats2_final
        File objects = finish_rqc.objects
    }
}



task stage {
   String container
   String target="raw.fastq.gz"
   String input_file

   command <<<
       set -e
       if [ $( echo ${input_file}|egrep -c "https*:") -gt 0 ] ; then
           wget ${input_file} -O ${target}
       else
           ln ${input_file} ${target} || cp ${input_file} ${target}
       fi
       # Capture the start time
       date --iso-8601=seconds > start.txt

   >>>

   output{
      File read = "${target}"
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
            File filtered = glob("filtered/*fastq.gz")[0]
            File json_out = filename_stat_json
            #String start = read_string("start.txt")
     }
}

task finish_rqc {
    File read
    File filtered_stats
    File filtered_stats2
    File filtered
    String container
    String git_url
    String informed_by
    String proj
    String prefix=sub(proj, ":", "_")
    String resource
    String url_root
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

       /scripts/generate_object_json.py \
             --type "nmdc:ReadQCAnalysisActivity" \
             --set read_QC_analysis_activity_set \
             --part ${proj} \
             -p "name=Read QC Activity for ${proj}" \
                was_informed_by=${informed_by} \
                started_at_time=${start} \
                ended_at_time=$end \
                execution_resource=${resource} \
                git_url=${git_url} \
             --url ${url_root}${proj}/qa/ \
             --extra stats.json \
             --inputs ${read} \
             --outputs \
             ${prefix}_filtered.fastq.gz "Reads QC result fastq (clean data)" "Filtered Sequencing Reads" \
                                         "Reads QC for ${proj}" \
             ${prefix}_filterStats.txt "Reads QC summary statistics" "QC Statistics" \
                                         "Reads QC summary for ${proj}" \

        #TODO:
        #Add set container & immediately send through validation parser and they pass
    >>>
    output {
        File filtered_final = "${prefix}_filtered.fastq.gz"
        File filtered_stats_final = "${prefix}_filterStats.txt"
        File filtered_stats2_final = "${prefix}_filterStats2.txt"
        File objects = "objects.json"
    }

    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
}
