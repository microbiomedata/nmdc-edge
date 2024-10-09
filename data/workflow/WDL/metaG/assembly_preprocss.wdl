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
        String memory=estimate_memory_int.memory
    }
}

task estimate_memory_int {
        input {
            Array[File] input_files
            String container
            String outdir
            String predicted_memory="pred_memory.txt"
        }

        command <<<
            reformat.sh in=~{input_files[0]} interleaved=t cardinality=true out=stdout.fq 1> /dev/null 2>| cardinality.txt
            num_kmers = `cat cardinality.txt|  awk '/Unique 31-mers:/{print $3}'`
            `awk 'BEGIN {print (($num_kmers*2.962e-08 + 1.630e+01) * 1.1)}'` > ~{predicted_memory}
            >>>

        runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }

        output {
            String memory = read_string(predicted_memory)
        }
    }