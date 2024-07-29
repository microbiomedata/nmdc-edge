
task remove_rrna{
	File rqc_clean_reads
	Map[String, File] sort_rna_db
	Int no_of_threads
	String DOCKER

	command <<<
		sortmerna --ref ${sort_rna_db["silva_arc_16s"]} --ref ${sort_rna_db["silva_arc_23s"]} --ref ${sort_rna_db["silva_bac_16s"]} --ref ${sort_rna_db["silva_bac_23s"]} --reads ${rqc_clean_reads} --aligned aligned --other unaligned --fastx --threads ${no_of_threads} --workdir tmp --paired --paired_in
	>>>
# --ref ${sort_rna_db["rfam_5S_db"]} --ref ${sort_rna_db["rfam_56S_db"]} --ref ${sort_rna_db["silva_arc_16s"]} --ref ${sort_rna_db["silva_arc_23s"]} --ref ${sort_rna_db["silva_bac_16s"]} --ref ${sort_rna_db["silva_bac_23s"]} --ref ${sort_rna_db["silva_euk_18s"]} --ref ${sort_rna_db["silva_euk_28s"]} --reads ${rqc_clean_reads} --aligned aligned --other unaligned --fastx --threads ${no_of_threads} --workdir tmp --paired --paired_in
	runtime {
		docker: DOCKER
	}

	output{
		File non_rrna_reads = "unaligned.fastq"
		File rrna_reads = "aligned.fastq"
	}
}


task bbduk_rrna{
	File rqc_clean_reads
	File ribo_kmer_file
	Int no_of_threads
	String DOCKER

	command <<<
		bbduk.sh -Xmx3g in=${rqc_clean_reads} out=filtered_R1.fastq out2=filtered_R2.fastq outm=ribo.fastq ref=${ribo_kmer_file} k=31 minlen=3 stats=stats.txt
	>>>

	runtime {
		docker: "microbiomedata/bbtools:38.96"
	}

	output{
		Array[File] non_rrna_reads = ["filtered_R1.fastq", "filtered_R2.fastq"]
		File rrna_reads = "ribo.fastq"
	}
}

