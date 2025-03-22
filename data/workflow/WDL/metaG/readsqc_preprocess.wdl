version 1.0

workflow readsqc_preprocess {
    input {
        Array[File] input_files
        Array[File] input_fq1
        Array[File] input_fq2
        String  container="bfoster1/img-omics:0.1.9"
        String  outdir
        Boolean input_interleaved
        Boolean shortRead
    }

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
        Array[String]? input_files_gz = if (input_interleaved) then gzip_int.input_files_gz else gzip_pe.input_files_gz
        Array[String]? input_files_prefix = if (input_interleaved) then gzip_int.input_files_prefix else gzip_pe.input_files_prefix
        Boolean? isIllumina = if (input_interleaved) then gzip_int.isIllumina else gzip_pe.isIllumina
    }
}

task gzip_input_int {
    input {
        Array[File] input_files
        String container
        String outdir
        String dollar ="$"
    }

    command <<<
        set -euo pipefail
        mkdir -p ~{outdir}
        if file --mime -b ~{input_files[0]} | grep gzip > /dev/null ; then
            cp ~{sep=" " input_files} ~{outdir}/
            header=`zcat ~{input_files[0]} | (head -n1; dd status=none of=/dev/null)`
        else
            cp ~{sep=" " input_files} ~{outdir}/
            gzip -f ~{outdir}/*.fastq
            header=`cat ~{input_files[0]} | (head -n1; dd status=none of=/dev/null)`
        fi
        # prefix array
        for i in ~{outdir}/*.gz
        do
            name=~{dollar}(basename "$i")
            prefix=~{dollar}{name%%.*}
            echo $prefix >> fileprefix.txt
        done    
        # simple format check 
        NumField=`echo $header | cut -d' ' -f2 | awk -F':' "{print NF}"`
        if [ $NumField -eq 4 ]; then echo "true"; else echo "false"; fi
    >>>

	runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }

	output{
        Array[String] input_files_gz = glob("~{outdir}/*.gz")
        Array[String] input_files_prefix = read_lines("fileprefix.txt")
        Boolean isIllumina = read_boolean(stdout())
	}
}


task interleave_reads{
    input {
        Array[File] input_files
        String output_file = "interleaved.fastq.gz"
        String container
    }

    command <<<
        set -euo pipefail
        if file --mime -b ~{input_files[0]} | grep gzip > /dev/null ; then
            paste <(gunzip -c ~{input_files[0]} | paste - - - -) <(gunzip -c ~{input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ~{output_file}
            echo ~{output_file}
        else
            if [[ "~{output_file}" == *.gz ]]; then
                paste <(cat ~{input_files[0]} | paste - - - -) <(cat ~{input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ~{output_file}
                echo ~{output_file}
            else
                paste <(cat ~{input_files[0]} | paste - - - -) <(cat ~{input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ~{output_file}.gz
                echo ~{output_file}.gz
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
