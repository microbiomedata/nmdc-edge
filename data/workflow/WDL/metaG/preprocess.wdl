workflow preprocess {
    Array[File] input_files
    Array[File] input_fq1
    Array[File] input_fq2
    String  container="bfoster1/img-omics:0.1.9"
    String outdir
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
        call interleave_reads {
		input: input_files = input_files
	}
        call gzip_input_int as gzip_pe {
        input:
            input_files=interleave_reads.out_fastq,
            container=container,
            outdir=outdir
        }

    }
    output {

       File input_file_gz = if (input_interleaved) then gzip_int.input_file_gz else gzip_pe.input_file_gz
    }
}

task gzip_input_int{
 	File input_file
	String container
	String outdir
	String filename = basename(input_file)

 	command<<<
        mkdir -p ${outdir}
        if file --mime -b ${input_file} | grep gzip > /dev/null ; then
            cp ${input_file} ${outdir}/

        else
            gzip -f ${input_file} > ${outdir}
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_file_gz = ${outdir}/${filename}.gz
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