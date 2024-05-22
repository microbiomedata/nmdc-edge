import "mbin_nmdc.wdl" as MetaMAGs

workflow main_workflow {
    String? outdir
    String  proj_name
    String contig_file
    String sam_file
    String gff_file
    String proteins_file
    String cog_file
    String ec_file
    String ko_file
    String pfam_file
    String tigrfam_file
    String cath_funfam_file
    String smart_file
    String supfam_file
    String product_names_file
    String gene_phylogeny_file
    String lineage_file
    File? map_file
    String? domain_file
    Int cpu=16
    Int threads=1
    Int pthreads=1
    String gtdbtk_db="/refdata/GTDBTK_DB"
    String checkm_db="/refdata/CheckM_DB/checkm_data_2015_01_16"
    String eukcc2_db="/refdata/eukcc2_db_ver_1.2"

    call MetaMAGs.nmdc_mags  as nmdc_mags {
        input: 
            proj=proj_name, 
            contig_file=contig_file,
            sam_file=sam_file, 
            gff_file=gff_file, 
            proteins_file=proteins_file,
            cog_file=cog_file,
            ec_file=ec_file,
            ko_file=ko_file,
            pfam_file=pfam_file,
            tigrfam_file=tigrfam_file,
            cath_funfam_file=cath_funfam_file,
            smart_file=smart_file,
            supfam_file=supfam_file,
            product_names_file=product_names_file,
            gene_phylogeny_file=gene_phylogeny_file,
            lineage_file=lineage_file,
            cpu=cpu, threads=threads,
            pthreads=pthreads,
            gtdbtk_db=gtdbtk_db, 
            checkm_db=checkm_db, 
            scratch_dir=outdir,
            eukcc2_db=eukcc2_db
    }
}
