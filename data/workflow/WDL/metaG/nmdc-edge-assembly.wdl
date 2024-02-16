import "jgi_assembly.wdl" as jgi_asm

workflow nmdc_edge_assembly{
    String? proj = "nmdc-edge-metaAsm"
    Array[File] input_file
    String? outdir
    String rename_contig_prefix="scaffold"
    Float uniquekmer=1000
    String bbtools_container="microbiomedata/bbtools:38.96"
    String spades_container="microbiomedata/spades:3.15.0"
    String quast_container="staphb/quast:5.2.0-slim"
    String memory="100g"
    String threads="4"
    Array[File] input_fq1=[]
    Array[File] input_fq2=[]


    call jgi_asm.jgi_metaASM as metaAssembly_call {
        input:
            input_file=input_file,
            input_fq1=input_fq1,
            input_fq2=input_fq2,
            outdir=outdir,
            rename_contig_prefix=rename_contig_prefix,
            uniquekmer=uniquekmer,
            bbtools_container=bbtools_container,
            spades_container=spades_container,
            memory=memory,
            threads=threads
    }

    call assembly_vis {
        input:
            contigs = metaAssembly_call.contig,
            container = quast_container,
            outdir = outdir,
            proj = proj

    }

    output {
        File contig = metaAssembly_call.contig
        File scaffold = metaAssembly_call.scaffold
        File agp=metaAssembly_call.agp
        File bam=metaAssembly_call.bam
        File samgz=metaAssembly_call.samgz
        File covstats=metaAssembly_call.covstats
        File asmstats=metaAssembly_call.asmstats
        File report_html = assembly_vis.report_html
        File report_txt = assembly_vis.report_txt
        File? final_contig = metaAssembly_call.final_contig
        File? final_scaffold = metaAssembly_call.final_scaffold
        File? final_agp = metaAssembly_call.final_agp
        File? final_covstat = metaAssembly_call.final_covstat
        File? final_samgz = metaAssembly_call.final_samgz
        File? final_bam = metaAssembly_call.final_bam
        File? final_asmstat = metaAssembly_call.final_asmstat
    }
}




task assembly_vis{
    
    File contigs
    String container
    String? outdir = "report"
    String proj
    String prefix=sub(proj, ":", "_")
    Int minContig = 500

    command<<<
        metaquast.py --version > version.txt
        metaquast.py -o ${outdir} -m ${minContig} --no-icarus --max-ref-number 0 ${contigs} 
        sed -e 's/.top-panel {/.top-panel {\n display:none;/' ${outdir}/report.html > ${outdir}/${prefix}_report.html
        mv ${outdir}/report.txt ${outdir}/${prefix}_report.txt

    >>>

    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
    
    output{
        File tool_version = "version.txt"
        File report_html = "${outdir}/${prefix}_report.html"
        File report_txt = "${outdir}/${prefix}_report.txt"
    }
    
}