workflow readsqc_preprocess {
    File? input_files
    File? input_fastq1
    File? input_fastq2
    String? outdir
    String bbtools_container="microbiomedata/bbtools:38.96"
    Boolean input_interleaved

    if (input_interleaved) {
        call gzip_input_int as gzip_int {
        input:
            input_files=input_files,
            container=bbtools_container
        }
    }

    if (!input_interleaved) {
        call gzip_input_pe as gzip_pe {
        input:
            input_fastq1=input_fastq1,
            input_fastq2=input_fastq2,
            container=bbtools_container
        }
    }
}

task gzip_input_int{
 	File input_files
	String container
    String dollar ="$"
    String output_file=""
 	command<<<
        if file --mime -b ${input_files} | grep gzip > /dev/null ; then
            f=${dollar}(basename ${input_files})
            output_file = ${dollar}{f%.gz}

        else
            gzip ${input_files}
            output_file = "${input_files}.gz"
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_files_gz = "${output_file}"
	}
}

task gzip_input_pe {
    File input_fastq1
    File input_fastq2
	String container
    String dollar ="$"

 	command<<<
        if file --mime -b ${input_fastq1} | grep gzip > /dev/null ; then
            gzip ${input_fastq1}
            gzip ${input_fastq2}
            output=${dollar}(basename input_fastq1)
        fi
 	>>>
	runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
	output{
        File input_fastq1_gz = "${input_fastq1}.gz"
        File input_fastq2_gz = "${input_fastq2}.gz"
	}
}
