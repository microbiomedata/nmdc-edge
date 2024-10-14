version 1.0

import "https://raw.githubusercontent.com/microbiomedata/metaAssembly/refs/tags/v1.0.5/shortReads_assembly.wdl" as jgi_asm
import "preprocess.wdl" as MetaAssembly_preprocess
import "assembly_preprocess.wdl" as MetaAssembly_memory_estimate

workflow nmdc_edge_assembly{
    input {
        Array[File] input_file
        String outdir
        String rename_contig_prefix="scaffold"
        Float  uniquekmer=1000
        String bbtools_container="microbiomedata/bbtools:38.96"
        String spades_container="microbiomedata/spades:3.15.0"
        String quast_container="staphb/quast:5.2.0-slim"
        String memory="100g"
        String threads="4"
        String proj = proj
        Boolean input_interleaved=true
        Array[File] input_fq1=[]
        Array[File] input_fq2=[]
    }

    call MetaAssembly_preprocess.preprocess as preprocess {
        input:
            input_files= input_file,
            outdir=outdir,
            input_interleaved=input_interleaved,
            input_fq1=input_fq1,
            input_fq2=input_fq2,
    
    }

    call MetaAssembly_memory_estimate.assembly_preprocess as assembly_preprocess {
        input:
            input_file = preprocess.input_file_gz,
            container = bbtools_container,
            outdir = outdir

    }


    call jgi_asm.jgi_metaASM as metaAssembly_call {
        input:
            input_file=preprocess.input_file_gz,
            proj=proj,
            rename_contig_prefix=rename_contig_prefix,
            bbtools_container=bbtools_container,
            spades_container=spades_container,
            memory=memory,
            threads=threads
    }

    call assembly_vis {
        input:
            contigs=metaAssembly_call.contig,
            container=quast_container,
            outdir=outdir,
            proj=proj

    }

    output {
        File contig = metaAssembly_call.contig
        File scaffold = metaAssembly_call.scaffold
        File agp=metaAssembly_call.agp
        File bam=metaAssembly_call.bam
        File samgz=metaAssembly_call.samgz
        File covstats=metaAssembly_call.covstats
        File asmstats=metaAssembly_call.asmstats
        File asminfo=metaAssembly_call.asminfo
        File report_html = assembly_vis.report_html
        File report_txt = assembly_vis.report_txt
        String predicted_memory = assembly_preprocess.memory
        String num_kmers = assembly_preprocess.num_kmers
    }
}

task assembly_vis{
    input {
        File contigs
        String container
        String? outdir = "report"
        String proj
        String prefix=sub(proj, ":", "_")
        Int minContig = 500
    }

    command<<<
        set -euo pipefail
        metaquast.py --version > version.txt
        metaquast.py -o ~{outdir} -m ~{minContig} --no-icarus --max-ref-number 0 ~{contigs} 
        if [ -f ~{outdir}/report.html ]; then
            sed -e 's/.top-panel {/.top-panel {\n display:none;/' ~{outdir}/report.html > ~{outdir}/~{prefix}_report.html
            mv ~{outdir}/report.txt ~{outdir}/~{prefix}_report.txt
        else
            echo "None of the assembly files contains correct contigs. contigs should >= 500 bp for the report" > ~{outdir}/~{prefix}_report.html
            echo "None of the assembly files contains correct contigs. contigs should >= 500 bp for the report" > ~{outdir}/~{prefix}_report.txt
        fi
    >>>

    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
    
    output{
        File tool_version = "version.txt"
        File report_html = "~{outdir}/~{prefix}_report.html"
        File report_txt = "~{outdir}/~{prefix}_report.txt"
    }  
}