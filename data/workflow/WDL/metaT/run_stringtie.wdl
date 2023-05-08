task run_stringtie{
	Int no_of_cpus
	File bam_fl_path
	String DOCKER

	command {
		stringtie -o out.gtf -p ${no_of_cpus} -A gene_abundan.gtf ${bam_fl_path}
	}

	output{
		File abun_info_fl = "gene_abundan.gtf"
		File out_info_fl = "out.gtf"
	}
	
	runtime {
		docker: DOCKER
	}
}


task stringtie_wref{
	Int no_of_cpus
	File bam_fl_path
	File ann_gff_fn
	String name_of_proj
	String DOCKER

	command {
		stringtie -e -G ${ann_gff_fn} -o ${name_of_proj}_out.gtf -p ${no_of_cpus} -A ${name_of_proj}_gene.gtf -C ${name_of_proj}.cov ${bam_fl_path}
		
	}
# 
	output{
		File cov_fl_nm = "${name_of_proj}.cov"
		# File abun_info_fl = "${name_of_proj}"_gene.gtf
		File out_info_fl = "${name_of_proj}_out.gtf"
		
	}
	
	runtime {
		docker: DOCKER
	}
}