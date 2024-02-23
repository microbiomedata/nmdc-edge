import "ReadbasedAnalysisTasks.wdl" as tasks

workflow ReadbasedAnalysis {
    Boolean enabled_tools_gottcha2 = true
    Boolean enabled_tools_kraken2 = true
    Boolean enabled_tools_centrifuge = true
    String db_gottcha2 = "/refdata/gottcha2/RefSeq-r90.cg.BacteriaArchaeaViruses.species.fna"
    String db_kraken2 = "/refdata/kraken2/"
    String db_centrifuge = "/refdata/centrifuge/p_compressed"
    Int cpu = 8
    String input_file
    String proj
    String prefix=sub(proj, ":", "_")
    Boolean? paired = false
    String bbtools_container="microbiomedata/bbtools:38.96"
    String? docker = "poeli/nmdc_taxa_profilers:1.0.5"

    call stage {
        input:
        container=bbtools_container,
        input_file=input_file
    }

    if (enabled_tools_gottcha2 == true) {
        call tasks.profilerGottcha2 {
            input: READS = stage.reads,
                   DB = db_gottcha2,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }

    if (enabled_tools_kraken2 == true) {
        call tasks.profilerKraken2 {
            input: READS = stage.reads,
                   PAIRED = paired,
                   DB = db_kraken2,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }

    if (enabled_tools_centrifuge == true) {
        call tasks.profilerCentrifuge {
            input: READS = stage.reads,
                   DB = db_centrifuge,
                   PREFIX = prefix,
                   CPU = cpu,
                   DOCKER = docker
        }
    }

    call make_info_file {
        input: docker = docker,
            enabled_tools_gottcha2 = enabled_tools_gottcha2,
            enabled_tools_kraken2 = enabled_tools_kraken2,
            enabled_tools_centrifuge = enabled_tools_centrifuge,
            db_gottcha2 = db_gottcha2,
            db_kraken2 = db_kraken2,
            db_centrifuge = db_centrifuge,
            docker = docker,
            gottcha2_info = profilerGottcha2.info,
            gottcha2_report_tsv = profilerGottcha2.report_tsv,
            gottcha2_info = profilerGottcha2.info,
            centrifuge_report_tsv = profilerCentrifuge.report_tsv,
            centrifuge_info = profilerCentrifuge.info,
            kraken2_report_tsv = profilerKraken2.report_tsv,
            kraken2_info = profilerKraken2.info,
        }

    call finish_reads {
            input:
            proj=proj,
            start=stage.start,
            input_file=stage.read_in,
            container="microbiomedata/workflowmeta:1.1.1",
            gottcha2_report_tsv=profilerGottcha2.report_tsv,
            gottcha2_full_tsv=profilerGottcha2.full_tsv,
            gottcha2_krona_html=profilerGottcha2.krona_html,
            centrifuge_classification_tsv=profilerCentrifuge.classification_tsv,
            centrifuge_report_tsv=profilerCentrifuge.report_tsv,
            centrifuge_krona_html=profilerCentrifuge.krona_html,
            kraken2_classification_tsv=profilerKraken2.classification_tsv,
            kraken2_report_tsv=profilerKraken2.report_tsv,
            kraken2_krona_html=profilerKraken2.krona_html,
            prof_info_file=make_info_file.profiler_info
        }

    output {
        File final_gottcha2_report_tsv = finish_reads.g2_report_tsv
        File final_gottcha2_full_tsv = finish_reads.g2_full_tsv
        File final_gottcha2_krona_html = finish_reads.g2_krona_html
        File final_centrifuge_classification_tsv = finish_reads.cent_classification_tsv
        File final_centrifuge_report_tsv = finish_reads.cent_report_tsv
        File final_centrifuge_krona_html = finish_reads.cent_krona_html
        File final_kraken2_classification_tsv = finish_reads.kr_classification_tsv
        File final_kraken2_report_tsv = finish_reads.kr_report_tsv
        File final_kraken2_krona_html = finish_reads.kr_krona_html
        File? info_file = finish_reads.rb_info_file
        String? info = make_info_file.profiler_info_text
    }

    meta {
        author: "Po-E Li, B10, LANL"
        email: "po-e@lanl.gov"
        version: "1.0.4"
    }
}


task stage {
   String container
   String input_file
   String? memory = "4G"
   String target = "staged.fastq.gz"
   String output1 = "input.left.fastq.gz"
   String output2 = "input.right.fastq.gz"

   command <<<
       set -e
       if [ $( echo ${input_file}|egrep -c "https*:") -gt 0 ] ; then
           wget ${input_file} -O ${target}
       else
           ln ${input_file} ${target} || cp ${input_file} ${target}
       fi

        reformat.sh -Xmx${default="10G" memory} in=${target} out1=${output1} out2=${output2}    
       # Capture the start time
       date --iso-8601=seconds > start.txt

   >>>

   output{
      File read_in = target
      Array[File] reads = [output1, output2]
      String start = read_string("start.txt")
   }
   runtime {
     cpu:  2
     maxRetries: 1
     docker: container
   }
}

task finish_reads {
    String input_file
    String container
    String proj
    String prefix=sub(proj, ":", "_")
    String start
    File prof_info_file
    File gottcha2_report_tsv
    File gottcha2_full_tsv
    File gottcha2_krona_html
    File centrifuge_classification_tsv
    File centrifuge_report_tsv
    File centrifuge_krona_html
    File kraken2_classification_tsv
    File kraken2_report_tsv
    File kraken2_krona_html

    command <<<

        set -e
        end=`date --iso-8601=seconds`
        # Set names
        if [[ $(head -2 ${gottcha2_report_tsv}|wc -l) -eq 1 ]] ; then
            echo "Nothing found in gottcha2 for ${proj} $end" >> ${prefix}_gottcha2_report.tsv
        else
            ln ${gottcha2_report_tsv} ${prefix}_gottcha2_report.tsv
        fi
        ln ${gottcha2_full_tsv} ${prefix}_gottcha2_full_tsv
        ln ${gottcha2_krona_html} ${prefix}_gottcha2_krona.html

        ln ${centrifuge_classification_tsv} ${prefix}_centrifuge_classification.tsv
        if [[ $(head -2 ${centrifuge_report_tsv}|wc -l) -eq 1 ]] ; then
            echo "Nothing found in centrifuge for ${proj} $end" >> ${prefix}_centrifuge_report.tsv
        else
            ln ${centrifuge_report_tsv} ${prefix}_centrifuge_report.tsv
        fi
        ln ${centrifuge_krona_html} ${prefix}_centrifuge_krona.html

        ln ${kraken2_classification_tsv} ${prefix}_kraken2_classification.tsv
        if [[ $(head -2 ${kraken2_report_tsv}|wc -l) -eq 1 ]] ; then
            echo "Nothing found in kraken2 for ${proj} $end" >> ${prefix}_kraken2_report.tsv
        else
            ln ${kraken2_report_tsv} ${prefix}_kraken2_report.tsv
        fi
        ln ${kraken2_krona_html} ${prefix}_kraken2_krona.html

        #info file
        ln ${prof_info_file} ${prefix}_profiler.info

    >>>

    output {
       File g2_report_tsv="${prefix}_gottcha2_report.tsv"
       File g2_full_tsv="${prefix}_gottcha2_full_tsv"
       File g2_krona_html="${prefix}_gottcha2_krona.html"
       File cent_classification_tsv="${prefix}_centrifuge_classification.tsv"
       File cent_report_tsv="${prefix}_centrifuge_report.tsv"
       File cent_krona_html="${prefix}_centrifuge_krona.html"
       File kr_classification_tsv="${prefix}_kraken2_classification.tsv"
       File kr_report_tsv="${prefix}_kraken2_report.tsv"
       File kr_krona_html="${prefix}_kraken2_krona.html"
       File rb_info_file="${prefix}_profiler.info"
    }

    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
}


task make_outputs{
    String outdir
    File? gottcha2_report_tsv
    File? gottcha2_full_tsv
    File? gottcha2_krona_html
    File? centrifuge_classification_tsv
    File? centrifuge_report_tsv
    File? centrifuge_krona_html
    File? kraken2_classification_tsv
    File? kraken2_report_tsv
    File? kraken2_krona_html
    String container

    command<<<

        mkdir -p ${outdir}/gottcha2
        cp ${gottcha2_report_tsv} ${gottcha2_full_tsv} ${gottcha2_krona_html} \
           ${outdir}/gottcha2
        mkdir -p ${outdir}/centrifuge
        cp ${centrifuge_classification_tsv} ${centrifuge_report_tsv} ${centrifuge_krona_html} \
           ${outdir}/centrifuge
        mkdir -p ${outdir}/kraken2
        cp ${kraken2_classification_tsv} ${kraken2_report_tsv} ${kraken2_krona_html} \
           ${outdir}/kraken2
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


task make_info_file {
    Boolean enabled_tools_gottcha2
    Boolean enabled_tools_kraken2
    Boolean enabled_tools_centrifuge
    String db_gottcha2
    String db_kraken2
    String db_centrifuge
    String docker
    File? gottcha2_report_tsv
    File? gottcha2_info
    File? centrifuge_report_tsv
    File? centrifuge_info
    File? kraken2_report_tsv
    File? kraken2_info
    String info_filename = "profiler.info"

    command <<<
        set -euo pipefail

        # generate output info file

        info_text="Taxonomy profiling tools and databases used: "
        echo $info_text > ${info_filename}

        if [[ ${enabled_tools_kraken2} == true ]]
        then
            software_ver=`cat ${kraken2_info}`
            #db_ver=`echo "${db_kraken2}" | rev | cut -d'/' -f 1 | rev`
            db_ver=`cat ${db_kraken2}/db_ver.info`
            info_text="Kraken2 v$software_ver (database version: $db_ver)"
            echo $info_text >> ${info_filename}
        fi

        if [[ ${enabled_tools_centrifuge} == true ]]
        then
            software_ver=`cat ${centrifuge_info}`
            db_ver=`cat $(dirname ${db_centrifuge})/db_ver.info`
            info_text="Centrifuge v$software_ver (database version: $db_ver)"
            echo $info_text >> ${info_filename}
        fi

        if [[ ${enabled_tools_gottcha2} == true ]]
        then
            software_ver=`cat ${gottcha2_info}`
            db_ver=`cat $(dirname ${db_gottcha2})/db_ver.info`
            info_text="Gottcha2 v$software_ver (database version: $db_ver)"
            echo $info_text >> ${info_filename}
        fi
    >>>

    output {
        File profiler_info = "${info_filename}"
        String profiler_info_text = read_string("${info_filename}")
    }
    runtime {
        docker: docker
        memory: "2G"
        cpu:  1
        maxRetries: 1
    }
}
