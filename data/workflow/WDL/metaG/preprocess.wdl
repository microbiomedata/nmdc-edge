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
        ## the zip() function generates an array of pairs, use .left and .right to access
        scatter(file in zip(input_fq1,input_fq2)){
            call interleave_reads {
                input:
                    input_files = [file.left,file.right],
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

       File? input_file_gz = if (input_interleaved) then gzip_int.input_file_gz else gzip_pe.input_file_gz
    }
}

task gzip_input_int{
 	Array[File?] input_files
	String container
	String outdir
	String filename = "output_fastq.gz"

 	command<<<
        mkdir -p ${outdir}
        if file --mime -b ${input_files[0]} | grep gzip > /dev/null ; then
            cat ${sep=" " input_files} > output_fastq.gz
        else
            cat ${sep=" " input_files} > input_files.fastq
            gzip -f input_files.fastq > output_fastq.gz
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_file_gz = "output_fastq.gz"
	}
}


task interleave_reads{

    Array[File] input_files
    String output_file = "interleaved.fastq.gz"
	String container

    command <<<
        if file --mime -b ${input_files[0]} | grep gzip > /dev/null ; then
        cat ${sep=" " input_files} > infile.fastq
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