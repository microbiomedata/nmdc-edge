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
            container=bbtools_container,
            outdir=outdir
        }
    }

    if (!input_interleaved) {
        call gzip_input_pe as gzip_pe {
        input:
            input_fastq1=input_fastq1,
            input_fastq2=input_fastq2,
            container=bbtools_container,
            outdir=outdir
        }
    }
}

task gzip_input_int{
 	File input_files
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
        File input_files_gz = "${outdir}/${out_file}.gz"
	}
}

task gzip_input_pe {
    File input_fastq1
    File input_fastq2
	String container
	String outdir
    String out_file1 = basename(input_fastq1,".gz")
    String out_file2 = basename(input_fastq2,".gz")

 	command<<<
        if file --mime -b ${input_fastq1} | grep gzip > /dev/null ; then
            mv ${input_fastq1} ${outdir}/
            mv ${input_fastq2} ${outdir}/
        else
            gzip -f ${input_fastq1}
            gzip -f ${input_fastq2}
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
