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
    output {
       Array[File] outputFiles = sra2fastq.outputFiles 
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

        ~{ 
           if defined(ext_dir) then 
               "mkdir -p " + ext_dir + "; cp -R " + outdir + "/* " + ext_dir 
           else 
               ":"
         }

         for acc in ~{sep=' ' accessions}; do  printf '%s\n' ~{outdir}/$acc/* >> file_list; done
    >>>
    output {
        Array[File] outputFiles = read_lines("file_list")
    }

    runtime {
        docker: "kaijli/sra2fastq:1.6.2"
        continueOnReturnCode: true
    }
}
