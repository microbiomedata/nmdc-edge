import "jgi_assembly.wdl" as MetaAssembly
import "preprocess.wdl" as MetaAssembly_preprocess

workflow main_workflow {
    Array[File] input_files
    String? outdir
    String rename_contig_prefix="scaffold"
    Float uniquekmer=1000
    String bbtools_container="microbiomedata/bbtools:38.92"
    String spades_container="microbiomedata/spades:3.15.0"
    String memory="100g"
    String threads="4"
    Boolean input_interleaved=true
    Array[File] input_fq1
    Array[File] input_fq2
    String prefix

    call MetaAssembly_preprocess.preprocess as preprocess {
        input:
            input_files= input_files,
		    outdir=outdir,
            input_interleaved=input_interleaved,
            input_fq1=input_fq1,
            input_fq2=input_fq2,
    }

    call MetaAssembly.jgi_metaASM as jgi_metaASM {
        input: 
            input_file=preprocess.input_file_gz,
            proj=prefix,
            outdir=outdir, 
            rename_contig_prefix=prefix,
            uniquekmer=uniquekmer, 
            bbtools_container=bbtools_container, 
            spades_container=spades_container, 
            memory=memory, 
            threads=threads
    }
}
