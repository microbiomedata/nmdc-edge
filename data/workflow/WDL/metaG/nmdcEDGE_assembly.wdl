version 1.0

import "https://raw.githubusercontent.com/microbiomedata/metaAssembly/refs/tags/v1.0.7/jgi_assembly.wdl" as jgi_asm
import "assembly_preprocess.wdl" as MetaAssembly_preprocess

workflow nmdc_edge_assembly{
    input {
        Array[String] input_file
        Array[File]   input_fq1=[]
        Array[File]   input_fq2=[]
        String outdir
        Float  uniquekmer=1000
        String bbtools_container="microbiomedata/bbtools:38.96"
        String spades_container="microbiomedata/spades:3.15.0"
        String quast_container="staphb/quast:5.2.0-slim"
        String memory="100g"
        String threads="4"
        String proj = proj
        Boolean input_interleaved=true
        Boolean shortRead=true
    }

    call MetaAssembly_preprocess.preprocess as preprocess {
        input:
            input_files= input_file,
            outdir=outdir,
            input_interleaved=input_interleaved,
            input_fq1=input_fq1,
            input_fq2=input_fq2,
    
    }

    call jgi_asm.jgi_metaAssembly as metaAssembly_call {
        input:
            input_files = select_all([preprocess.input_file_gz]),
            proj=proj,
            memory=memory,
            threads=threads,
            shortRead=shortRead
    }

    call assembly_vis {
        input:
            contigs=if(shortRead) then metaAssembly_call.sr_contig else metaAssembly_call.lr_contigs,
            container=quast_container,
            outdir=outdir,
            proj=proj

    }

    output {
        File? contig = if(shortRead) then metaAssembly_call.sr_contig else metaAssembly_call.lr_contigs
        File? scaffold = if(shortRead) then metaAssembly_call.sr_scaffold else metaAssembly_call.lr_scaffolds
        File? agp= if(shortRead) then metaAssembly_call.sr_agp else metaAssembly_call.lr_agp
        File? bam= if(shortRead) then metaAssembly_call.sr_bam else metaAssembly_call.lr_bam 
        File? samgz= if(shortRead) then metaAssembly_call.sr_samgz else metaAssembly_call.lr_sam
        File? covstats= if(shortRead) then metaAssembly_call.sr_covstats else metaAssembly_call.lr_basecov
        File? asmstats= metaAssembly_call.stats
        File? asminfo= if(shortRead) then metaAssembly_call.sr_asminfo else metaAssembly_call.lr_asminfo
        File report_html = assembly_vis.report_html
        File report_txt = assembly_vis.report_txt
    }
}

task assembly_vis{
    input {
        File? contigs
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