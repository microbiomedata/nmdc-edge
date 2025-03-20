version 1.0

workflow assembly_output {
    input {
        File?  contigs
        String container
        String outdir
        String proj

    }
    call assembly_vis {
        input:
            contigs=contigs,
            container=container,
            outdir=outdir,
            proj=proj

    }
    output {
        File report_html = assembly_vis.report_html
        File report_txt = assembly_vis.report_txt
    }
}

task assembly_vis{
    input {
        File?   contigs
        String  container
        String? outdir = "report"
        String  proj
        String  prefix=sub(proj, ":", "_")
        Int     minContig = 500
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