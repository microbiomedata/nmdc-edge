# SRA2FastQ workflow
# Declare WDL version 1.0 if working in Terra
version 1.0
workflow sra {
    input {
        Array[String] accessions
        String outdir
        String? ext_dir
        Boolean? clean
        String? platform_restrict
        Int? filesize_restrict
        Int? runs_restrict
    }

    call sra2fastq{
        input:
        accessions = accessions,
        outdir = outdir,
        ext_dir = ext_dir,
        clean = clean,
        platform_restrict = platform_restrict,
        filesize_restrict = filesize_restrict,
        runs_restrict = runs_restrict

    }
}

task sra2fastq {
    input {
        Array[String] accessions
        String outdir
        String? ext_dir
        Boolean? clean
        String? platform_restrict
        Int? filesize_restrict
        Int? runs_restrict
    }
     command <<<

        sra2fastq.py ~{sep=' ' accessions} ~{"--outdir=" + outdir}  ~{true=" --clean True" false="" clean} ~{" --platform_restrict=" + platform_restrict} ~{" --filesize_restrict=" + filesize_restrict} ~{" --runs_restrict=" + runs_restrict}
        mkdir -p ~{ext_dir}
        mv ~{outdir + "/*"} ~{ext_dir}
    >>>
    output {
        Array[File] outputFiles = glob("${outdir}/*")
    }

    runtime {
        docker: "kaijli/sra2fastq:1.6"
        continueOnReturnCode: true
    }
}