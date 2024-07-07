task parse_intergenic{
	File annotation_gff
	Int intergenic_len=10
	String DOCKER

	command {
	   python /parse_intergenic.py ${annotation_gff} ${intergenic_len}
	}
        
	output{
           File filtered_intergenic_gff = "filtered_intergenic.gff" 
        }

        runtime {
                time: "2:00:00"
                docker: DOCKER
                memory: "120 GiB"
        }

        meta {
                author: "Migun Shakya, B10, LANL"
                email: "migun@lanl.gov"
        }
}
task featurecount{
	Int no_of_cpu
	String project_name
	File gff_file_path
	File bam_file_path
	String name_of_feat
	String DOCKER

	command {
            featureCounts -a ${gff_file_path}  -O -p -s 1 --countReadPairs -g ID -t ${name_of_feat} -T ${no_of_cpu} -o ${name_of_feat}_sense.count ${bam_file_path}
	    featureCounts -a ${gff_file_path}  -O -p -s 2 --countReadPairs -g ID -t ${name_of_feat} -T ${no_of_cpu} -o ${name_of_feat}_antisense.count ${bam_file_path}
	   # cat ${name_of_feat}_antisense.count | grep -v "#" | grep -v "Geneid" > ${name_of_feat}_antisense_rm_head.count
	   # cat ${name_of_feat}_sense.count ${name_of_feat}_antisense_rm_head.count > ${name_of_feat}.count
	   #cat ${name_of_feat}_sense.count > sense.count
	   #cat ${name_of_feat}_antisense.count > antisense.count 
	}

	output{
		File ct_tbl = "${name_of_feat}_sense.count"
		File ct_tbl2 = "${name_of_feat}_antisense.count"
	}

	runtime {
		time: "2:00:00"
		docker: DOCKER
		memory: "120 GiB" 
	}

	meta {
		author: "Migun Shakya, B10, LANL"
		email: "migun@lanl.gov"
	}

}

task add_feature_types {
        File sense
        File antisense
	String proj
	String DOCKER

        command {
                 
            python /metaT_sort_rpkm.py -sj ${sense} -aj ${antisense} -id ${proj}
        }

        output{
		File filtered_sense_json = "${proj}_sense_counts.json"
		File filtered_antisense_json = "${proj}_antisense_counts.json"
                File full_features_tsv = "rpkm_sorted_features.tsv"
                File  top100 = "top100_features.json"
        }

        runtime {
                time: "2:00:00"
                docker: DOCKER
                memory: "120 GiB"
        }

        meta {
                author: "Migun Shakya, B10, LANL"
                email: "migun@lanl.gov"
        }

}
