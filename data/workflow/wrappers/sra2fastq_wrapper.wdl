version 1.0
import "sra2fastq.wdl" as sra2fastq

workflow main_workflow {
    input {
        Array[String] accessions
        Boolean clean=true
        String outdir
    }

    call sra2fastq.sra as sra {
        input: 
            accessions=accessions,
            clean=clean,
            outdir=outdir
    }
}
