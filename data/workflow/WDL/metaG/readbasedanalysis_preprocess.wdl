workflow preprocess {
    File? input_file
    File? input_fq1
    File? input_fq2
    String  container="bfoster1/img-omics:0.1.9"
    String outdir


    call gzip_input_int as gzip_int {
    input:
        input_file=input_file,
        container=container,
        outdir=outdir
    }

    output {

       File? input_file_gz = if (input_interleaved) then gzip_int.input_file_gz else gzip_pe.input_file_gz
    }
}

task gzip_input_int{
 	File input_file
	String container
	String outdir
	String filename = "output_fastq.gz"

 	command<<<
        mkdir -p ${outdir}
        if file --mime -b ${input_file} | grep gzip > /dev/null ; then
            basename ${input_file} .gz
            cp  ${input_file} ${outdir}/${filename}

        else
            gzip -f ${input_file} > "${outdir}/{$filename}"
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_file_gz = "${outdir}/${filename}"
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