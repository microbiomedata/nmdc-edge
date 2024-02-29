workflow preprocess {
    Array[File] input_files
    String  container="bfoster1/img-omics:0.1.9"
    String outdir
    Boolean paired

    if (!paired) {
        call gzip_input_int as gzip_int {
        input:
            input_files=input_files,
            container=container
        }
    }
    if (paired) {
        call interleave_reads {
                input:
                    input_files = input_files,
                    container = container
           }
        call gzip_input_pe as gzip_pe {
        input:
            input_file=interleave_reads.out_fastq,
            container=container
        }
    }
    output {

       File? input_file_gz = if (paired) then gzip_pe.input_file_gz else gzip_int.input_file_gz
    }
}

task gzip_input_int{
    # input files are an array of interleaved fastqs
 	Array[File] input_files
	String container
	String filename = "output_fastq.gz"

 	command<<<
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

task gzip_input_pe{
# input files are a single pair of paired end reads that has been interleaved
 	File input_file
	String container
	String filename = "output_fastq.gz"

 	command<<<
        if file --mime -b ${input_file} | grep gzip > /dev/null ; then
            cp ${input_file} output_fastq.gz
        else
            gzip -f ${input_file} > output_fastq.gz
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