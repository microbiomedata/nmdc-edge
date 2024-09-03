version 1.0

workflow readsqc_output {
    input {
        Array[File] input_files
        Array[String] input_files_prefix
        File filtered_stats_final
        File filtered_stats2_final
        File rqc_info
        String? outdir
        String bbtools_container="microbiomedata/bbtools:38.96"
        String vis_container="microbiomedata/fastqc_vis:1.0"
    }

    call make_output {
        input: 
        outdir=outdir,
        input_files=input_files,
        input_files_prefix=input_files_prefix,
        filtered_stats_final=filtered_stats_final,
        filtered_stats2_final=filtered_stats2_final,
        rqc_info=rqc_info,
        container=bbtools_container
    }
    call fastqc_report {
        input: 
        outdir=outdir,
        input_files=input_files,
        input_files_prefix=input_files_prefix,
        filtered_stats2_final=filtered_stats2_final,
        container=vis_container
    }
    output {
        File fastqc_html = fastqc_report.fastqc_html
        Array[String] fastq_files = make_output.fastq_files
    }
}


task fastqc_report{
    input{
        String? outdir
        Array[String] input_files_prefix
        Array[File] input_files
        File filtered_stats2_final
        Int file_num = length(input_files_prefix) 
        String container
        String dollar ="$"
    }

    command<<<
        set -euo pipefail

        mkdir -p output
        ARRAY=(~{sep=" " input_files_prefix})
        ARRAYFastq=(~{sep=" " input_files})
        for (( i = 0; i < ~{file_num}; i++ ))
        do
            f=~{dollar}(basename ~{dollar}{ARRAY[$i]})
            dir=~{dollar}(dirname ~{dollar}{ARRAYFastq[$i]})
            prefix=~{dollar}{ARRAY[$i]}
            ln ~{dollar}{ARRAYFastq[$i]} $prefix.fastq.gz
            fastqc -q -o output --dir $PWD $prefix.fastq.gz
            mkdir -p ~{outdir}/$prefix
            qc_summary.py --input $dir/*filterStats2.txt  --output ~{outdir}/$prefix/qc_summary.html
        done

        multiqc -z -o output output

        cp output/multiqc_report.html ~{outdir}/multiqc_report.html
    >>>

	runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
	output{
		File fastqc_html = "~{outdir}/multiqc_report.html"
	}
}

task make_output{
    input{
        String? outdir
        Array[String] input_files_prefix
        Array[File] input_files
        File filtered_stats_final
        File filtered_stats2_final
        File rqc_info
        Int file_num = length(input_files_prefix)
        String dollar ="$"
        String container
    }

 	command <<<
        set -euo pipefail
        mkdir -p ~{outdir}
        ARRAY=(~{sep=" " input_files_prefix})
        ARRAYFastq=(~{sep=" " input_files})
        for (( i = 0; i < ~{file_num}; i++ ))
        do
            f=~{dollar}(basename ~{dollar}{ARRAY[$i]})
            dir=~{dollar}(dirname ~{dollar}{ARRAYFastq[$i]})
            prefix=~{dollar}{ARRAY[$i]}
            mkdir -p ~{outdir}/$prefix
            cp -f ~{dollar}{ARRAYFastq[$i]} ~{outdir}/$prefix/$prefix.filtered.gz
            cp -f $dir/*filterStats.txt  ~{outdir}/$prefix/filterStats.txt
            cp -f $dir/*filterStats2.txt  ~{outdir}/$prefix/filterStats2.txt
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
