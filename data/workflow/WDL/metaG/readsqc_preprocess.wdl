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
            container=bbtools_container,
            outdir=outdir,
            shortRead=shortRead
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
            container=bbtools_container,
            outdir=outdir,
            shortRead=true
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
        String  container
        String  outdir
        String  dollar ="$"
        Int     memory = 10
        Boolean shortRead
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
            # Validate gzipped file for shortreads
            if [ "~{shortRead}" = "true" ]; then
                reformat.sh -Xmx~{memory}G verifypaired=t in=~{outdir}/merged.fastq.gz
            fi
            
            header=$(zcat ~{outdir}/merged.fastq.gz | (head -n1; dd status=none of=/dev/null))
            echo "merged.fastq" > fileprefix.txt
        else
            # gzip fastqs
            if ls ~{outdir}/*.fastq 1> /dev/null 2>&1; then
                gzip -f ~{outdir}/*.fastq
            fi

            # Validate gzipped file
            for file in ~{outdir}/*.gz; do
                if [ "~{shortRead}" = "true" ]; then
                    reformat.sh -Xmx~{memory}G verifypaired=t in="$file"
                fi
            done

            if file --mime -b ~{input_files[0]} | grep -q gzip; then
                header=$(zcat ~{input_files[0]} \
                        | (head -n1; dd status=none of=/dev/null))
            else
                header=$(cat ~{input_files[0]} \
                        | (head -n1; dd status=none of=/dev/null))
            fi

            # prefix array
            for i in ~{outdir}/*.gz;
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
        String target_reads_1="raw_reads_1.fastq.gz"
        String target_reads_2="raw_reads_2.fastq.gz"
        String container
        Int memory = 10
    }

    command <<<
        set -euo pipefail

        # Check if file is gzip
        if file --mime -b ~{input_files[0]} | grep -q gzip ; then
            # Check if filename ends with .gz
            if [[ ~{input_files[0]}  != *.gz ]]; then
                mv ~{input_files[0]} ~{input_files[0]}.gz
            if [[ ~{input_files[1]}  != *.gz ]]; then
                mv ~{input_files[1]} ~{input_files[1]}.gz
            reformat.sh in=~{input_files[0]}.gz in2=~{input_files[1]}.gz out=~{output_file}
        else
            reformat.sh in=~{input_files[0]} in2=~{input_files[1]} out=~{output_file}
        fi

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
