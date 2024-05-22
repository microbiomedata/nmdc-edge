import "metaT.wdl" as Metatranscriptome

workflow main_workflow {
    String proj
    File? input_file
    File? input_fq1
    File? input_fq2
    Boolean input_interleaved
    String git_url
    String url_root
    String outdir
    String resource
    String database
    String activity_id
    String informed_by
    Int threads
    File metat_folder

    call Metatranscriptome.nmdc_metat as nmdc_metat {
        input: 
            proj=proj,
            input_file=input_file,
            input_interleaved=input_interleaved, 
            input_fq1=input_fq1, 
            input_fq2=input_fq2,
            git_url=git_url,
            url_root=url_root,
            outdir=outdir,
            resource=resource,
            database=database,
            activity_id=activity_id,
            informed_by=informed_by,
            threads=threads,
            metat_folder=metat_folder
    }
}
