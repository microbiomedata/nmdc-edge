workflow readsqc_preprocess {
    Array[File] input_files
    Array[File] input_fq1
    Array[File] input_fq2
    String  container="bfoster1/img-omics:0.1.9"
    String? outdir
    Boolean input_interleaved

    if (input_interleaved) {
        call gzip_input_int as gzip_int {
        input:
            input_files=input_files,
            container=container,
            outdir=outdir
        }
    }

    if (!input_interleaved) {
        scatter(file in zip(input_fq1,input_fq2)){
             call interleave_reads {
                 input:
                     input_files = [file.left,file.right],
                     output_file = basename(file.left) + "_" + basename(file.right),
	                 container = container
             }
        }
        call gzip_input_int as gzip_pe {
        input:
            input_files=interleave_reads.out_fastq,
            container=container,
            outdir=outdir
        }

    }
    output {

       Array[File] input_files_gz = if (input_interleaved) then gzip_int.input_files_gz else gzip_pe.input_files_gz
    }
}

task gzip_input_int{
 	Array[File] input_files
	String container
	String outdir
    String out_file = basename(input_files,".gz")

 	command<<<
        mkdir -p ${outdir}
        if file --mime -b ${input_files} | grep gzip > /dev/null ; then
            mv ${input_files} ${outdir}/

        else
            gzip -f ${input_files}
            mv "${input_files}.gz" ${outdir}/
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        Array[File] input_files_gz = glob("${outdir}/${out_file}*.gz")
	}
}

task gzip_input_pe {
    File input_fq1
    File input_fq2
	String container
	String outdir
    String out_file1 = basename(input_fq1,".gz")
    String out_file2 = basename(input_fq2,".gz")

 	command<<<
        if file --mime -b ${input_fq1} | grep gzip > /dev/null ; then
            mv ${input_fq1} ${outdir}/
            mv ${input_fq2} ${outdir}/
        else
            gzip -f ${input_fq1}
            gzip -f ${input_fq2}
            mv "${input_fq1}.gz" ${outdir}/
            mv "${input_fq2}.gz" ${outdir}/
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_fastq1_gz = "${outdir}/${out_file1}.gz"
        File input_fastq2_gz = "${outdir}/${out_file2}.gz"
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
