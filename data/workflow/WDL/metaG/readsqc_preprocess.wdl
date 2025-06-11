version 1.0

workflow readsqc_preprocess {
    input {
        Array[File] input_files
        Array[File] input_fq1
        Array[File] input_fq2
        String  container="bfoster1/img-omics:0.1.9"
        String  bbtools_container="microbiomedata/bbtools:38.96"
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
                container = bbtools_container
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
        cp ~{sep=" " input_files} ~{outdir}/

        needs_merge=false
        for f in ~{outdir}/*; 
        do
            base=$(basename "$f")
            if [[ ! "$base" =~ \.fastq$ && ! "$base" =~ \.gz$ ]]; then
                needs_merge=true
            fi
        done

        if $needs_merge; then
            cat ~{outdir}/* > ~{outdir}/merged.fastq.gz
            header=$(zcat ~{outdir}/merged.fastq.gz | (head -n1; dd status=none of=/dev/null))
            echo "merged.fastq" > fileprefix.txt
        else
            if file --mime -b ~{input_files[0]} | grep gzip > /dev/null ; then
                header=$(zcat ~{input_files[0]} | (head -n1; dd status=none of=/dev/null))
            else
                gzip -f ~{outdir}/*.fastq
                header=$(cat ~{input_files[0]} | (head -n1; dd status=none of=/dev/null))
            fi
            # prefix array
            for i in ~{outdir}/*.gz ~{outdir}/*.fastq;
            do
                name=~{dollar}(basename "$i")
                prefix=~{dollar}{name%%.*}
                echo $prefix >> fileprefix.txt
            done
        fi

        NumField=$(echo $header | cut -d' ' -f2 | awk -F':' '{print NF}')
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
        Int memory = 10
    }

    command <<<
        set -euo pipefail
        reformat.sh in=~{input_files[0]} in2=~{input_files[1]} out=~{output_file}

        # Validate that the read1 and read2 files are sorted correctly
        reformat.sh -Xmx~{memory}G verifypaired=t in=~{output_file}
        echo ~{output_file}
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
