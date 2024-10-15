version 1.0

workflow assembly_preprocess {
    input {
        File? input_file
        String  container="microbiomedata/bbtools:38.96"
        String outdir
    }

    call estimate_memory as mem_estimate{
        input:
            input_file = input_file,
            container = container,
            outdir = outdir
    }

    output {
        String memory = mem_estimate.memory
        String num_kmers = mem_estimate.num_kmers
    }
}

task estimate_memory {
        input {
            File? input_file
            String container
            String outdir
            String predicted_memory="pred_memory.txt"
            String num_kmers_file="num_kmers.txt"
        }

        command <<<
            reformat.sh in=~{input_file} interleaved=t cardinality=true out=stdout.fq 1> /dev/null 2>| cardinality.txt
            num_kmers=`cat cardinality.txt|  awk '/Unique 31-mers:/{print $3}'`
            pred_mem=`awk 'BEGIN {print (($num_kmers*2.962e-08 + 1.630e+01) * 1.1)}'`
            pred_mem=`cat cardinality.txt|  awk '/Unique 31-mers:/{print $3}'`
            pred_mem+='g'
            echo "$pred_mem" > ~{predicted_memory}
            echo "$num_kmers" > ~{num_kmers_file}
            >>>

        runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }

        output {
            String memory = read_string(predicted_memory)
            String num_kmers = read_string(num_kmers_file)
        }
    }