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
            container=bbtools_container
        }
    }
}

task gzip_input_int{
 	File input_files
	String container
	String outdir
    String dollar ="$"
    String f = basename(input_files)+".gz"
 	command<<<
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
        File input_files_gz = "${outdir}/${f}"
	}
}

task gzip_input_pe {
    File input_fastq1
    File input_fastq2
	String container
    String dollar ="$"

 	command<<<
        if file --mime -b ${input_fastq1} | grep gzip > /dev/null ; then
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
        File input_fastq1_gz = "${input_fastq1}.gz"
        File input_fastq2_gz = "${input_fastq2}.gz"
	}
}
