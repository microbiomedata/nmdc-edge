# SRA2FastQ workflow
# Declare WDL version 1.0 if working in Terra
version 1.0
workflow sra {
    input {
        Array[String] accessions
        String? OUTDIR
        Boolean? clean
        String? platform_restrict
        Int? filesize_restrict
        Int? runs_restrict
    }

    call sra2fastq{
        input:
        accessions = accessions,
        OUTDIR = OUTDIR,
        clean = clean,
        platform_restrict = platform_restrict,
        filesize_restrict = filesize_restrict,
        runs_restrict = runs_restrict

    }
}

task sra2fastq {
    input {
        Array[String] accessions
        String? OUTDIR
        Boolean? clean
        String? platform_restrict
        Int? filesize_restrict
        Int? runs_restrict
    }
     command <<<

        sra2fastq.py ~{sep=' ' accessions} ~{"--outdir=" + OUTDIR}  ~{true=" --clean True" false="" clean} ~{" --platform_restrict=" + platform_restrict} ~{" --filesize_restrict=" + filesize_restrict} ~{" --runs_restrict=" + runs_restrict}

    >>>
    output {
        Array[File] outputFiles = glob("${OUTDIR}/*")
    }

    runtime {
        docker: "kaijli/sra2fastq:1.6"
        continueOnReturnCode: true
    }