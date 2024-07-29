task megahit_assembly{
	Array[File] rqc_clean_reads
	String assem_out_fdr
	String assem_out_prefix
    # String prefix="contig"
	Int no_of_cpus=32
	String DOCKER

#  parameter from https://www.nature.com/articles/s41597-019-0132-4
	command <<<
		megahit --12 ${rqc_clean_reads[0]}  -t ${no_of_cpus} -o out/ --out-prefix mh --k-list 23,43,63,83,103,123
        mkdir -p ${assem_out_fdr}
		cat out/mh.contigs.fa |sed 's/>.*_/>${assem_out_prefix}_/'|sed 's/ .*//' > ${assem_out_fdr}/${assem_out_prefix}.contigs.fa
	>>>

	meta {
		description: "assemble transcript"
	}

	runtime {
		docker: DOCKER
		cpu: no_of_cpus
	}

	output{
		File assem_fna_file = "${assem_out_fdr}/${assem_out_prefix}.contigs.fa"
	}
}

