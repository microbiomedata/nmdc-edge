workflow jgi_assembly_output {
    String? outdir
    File contigs
    File scaffolds
    File agp
    File bam
    File samgz
    File covstats
    File asmstats
    String contigs_name=basename(contigs)
    String scaffolds_name=basename(scaffolds)
    String agp_name=basename(agp)
    String bam_name=basename(bam)
    String samgz_name=basename(samgz)
    String covstats_name=basename(covstats)
    String asmstats_name=basename(asmstats)
    String container

    call make_output {
        input:
        container=container,
        contigs=contigs,
        scaffolds=scaffolds,
        agp=agp,
        bam=bam,
        samgz=samgz,
        covstats=covstats,
        asmstats=asmstats,
        contigs_name=contigs_name
        scaffolds_name=scaffolds_name
        agp_name=agp_name
        bam_name=bam_name
        samgz_name=samgz_name
        covstats_name=covstats_name
        asmstats_name=asmstats_name
        container=container
    }
    output {
        File contig=finish_asm.outcontigs
        File scaffold=finish_asm.outscaffolds
        File agp=finish_asm.outagp
        File bam=finish_asm.outbam
        File samgz=finish_asm.outsamgz
        File covstats=finish_asm.outcovstats
        File asmstats=finish_asm.outasmstats
        File asminfo=make_info_file.asminfo
    }

}

task make_output{
        String outdir
        File contigs
        File scaffolds
        File agp
        File bam
        File samgz
        File covstats
        File asmstats
        String contigs_name=basename(contigs)
        String scaffolds_name=basename(scaffolds)
        String agp_name=basename(agp)
        String bam_name=basename(bam)
        String samgz_name=basename(samgz)
        String covstats_name=basename(covstats)
        String asmstats_name=basename(asmstats)
        String container

 	command{
 		if [ ! -z ${outdir} ]; then
 			mkdir -p ${outdir}
 			cp ${contigs} ${scaffolds} ${agp} ${bam} \
 			   ${samgz} ${covstats} ${asmstats} ${outdir}
 			chmod 764 -R ${outdir}
 		fi
 	}
	runtime {
                docker: container
		memory: "1 GiB"
		cpu:  1
	}
	output{
		File? outcontigs = "${outdir}/${contigs_name}"
		File? outscaffolds = "${outdir}/${scaffolds_name}"
		File? outagp = "${outdir}/${agp_name}"
		File? outbam = "${outdir}/${bam_name}"
		File? outsamgz = "${outdir}/${samgz_name}"
		File? outcovstats = "${outdir}/${covstats_name}"
		File? outasmstats = "${outdir}/${asmstats_name}"
	}
}