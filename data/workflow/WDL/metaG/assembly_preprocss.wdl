version 1.0

workflow assembly_preprocess {
    input {
        Array[File] input_files
        Array[File] input_fq1
        Array[File] input_fq2
        String  container="microbiomedata/bbtools:38.96"
        String outdir
        Boolean input_interleaved
    }

    call estimate_memory_int {
        input:
            input_files = input_files,
            container = container,
            outdir = outdir
    }

    output {
        String num_kmers=estimate_memory_int.num_kmers
    }
}

task estimate_memory_int {
        input {
            Array[File] input_files
            String container
            String outdir
            String dollar ="$"
        }

        command <<<
            reformat.sh in=${input_files} interleaved=t cardinality=true out=stdout.fq 1> /dev/null 2>| cardinality.txt
            kmers=grep 'Unique' cardinality.txt  | awk -F'\t' '{print $2}'
            echo $kmers
            >>>

        runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }

        output {
            String num_kmers = "${kmers}"
        }
    }