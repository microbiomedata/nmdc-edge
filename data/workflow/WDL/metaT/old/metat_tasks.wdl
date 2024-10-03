task clean_gff{
	File gff_file_path
	String DOCKER
	command <<<
    # removing special characters that featurecount didnt like when parsing gff
		sed "s/\'//g" ${gff_file_path} | sed "s/-/_/g"  > clean.gff

	>>>

	output{
		File cln_gff_fl = "clean.gff"
	}
	
	runtime {
		docker: DOCKER
	}
}

task extract_feats{
	File gff_file_path
	String DOCKER

	command <<<
		awk -F'\t' '{print $3}' ${gff_file_path} | sort | uniq
	>>>

	output{
		Array[String] feats_in_gff = read_lines(stdout())
	}

	runtime {
		docker: DOCKER
	}
}

task create_gffdb{
	File gff_file_path
	String DOCKER

	command <<<
		python <<CODE
		import gffutils
		gffutils.create_db("${gff_file_path}", dbfn="gff.db", force=True, keep_order=True, merge_strategy="create_unique")
		CODE
	>>>

	output{
		File gff_db_fn = "gff.db"
	}
	runtime {
		docker: DOCKER
	}
}


task collect_output{
	Array[File] out_files
	String prefix
	String DOCKER

	command <<<
		python <<OEF
		import json
		out_file = "${prefix}" + "_sense_out.json"
		result = []
		list_of_fls = ['${sep="','" out_files}']
		for f in list_of_fls:
			with open(f, "rb") as infile:
				result.append(json.load(infile))
		with open(out_file, "w") as outfile:
			json.dump(result, outfile, indent=4)
		OEF
	>>>

	runtime {
		docker: DOCKER
	}

	output{
		File out_json_file = prefix + "_sense_out.json"
	}
}

task collect_output2{
        Array[File] out_files
        String prefix
        String DOCKER

        command <<<
                python <<OEF
                import json
                out_file = "${prefix}" + "_antisense_out.json"
                result = []
                list_of_fls = ['${sep="','" out_files}']
                for f in list_of_fls:
                        with open(f, "rb") as infile:
                                result.append(json.load(infile))
                with open(out_file, "w") as outfile:
                        json.dump(result, outfile, indent=4)
                OEF
        >>>

        runtime {
                docker: DOCKER
        }

        output{
                File out_json_file2 = prefix + "_antisense_out.json"
        }
}


task split_fastq{
	File intleave_fq_fl

	command <<<
		cat ${intleave_fq_fl} | paste - - - - - - - - | tee | cut -f 1-4 | tr "\t" "\n" | egrep -v '^$' > R1.fastq
		cat ${intleave_fq_fl} | paste - - - - - - - - | tee | cut -f 5-8 | tr "\t" "\n" | egrep -v '^$' > R2.fastq
		
	>>>

	output{
		File out_r1_file = "R1.fastq"
		File out_r2_file = "R2.fastq"
	}
}

task stage {
   String container
   String proj
   String prefix=sub(proj, ":", "_")
   String target="${prefix}.fastq.gz"
   String input_file

   command{
       set -e
       if [ $( echo ${input_file}|egrep -c "https*:") -gt 0 ] ; then
           wget ${input_file} -O ${target}
       else
           cp ${input_file} ${target}
       fi
       date --iso-8601=seconds > start.txt
   }

   output{
      File read = "${target}"
      String start = read_string("start.txt")
      String pref = "${prefix}"
   }
   runtime {
     memory: "1 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }
}

task split_interleaved_fastq{
    File reads
    String container
    String? memory = "4G"
    String output1 = "input.left.fastq.gz"
    String output2 = "input.right.fastq.gz"

    runtime {
        docker: container
        mem: "4 GiB"
        cpu:  1
    }
    command {
         reformat.sh -Xmx${default="10G" memory} in=${reads} out1=${output1} out2=${output2}
    }

    output {
            Array[File] outFastq = [output1, output2]
    }
}


task make_interleaved {
   File input1
   File input2
   String pref
   String container

   command{
      reformat.sh in1=${input1} in2=${input2} out="${pref}.fastq.gz"
   }

   output{
      File out_fastq = "${pref}.fastq.gz"
   }
   runtime {
     memory: "1 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }
}

task finish_metat {
   String container
   String start
   String informed_by
   File read
   File filtered 
   File filtered_stats
   File filtered_stats2
   File fasta
   String resource
   String url_root
   String git_url
   String proj
   String prefix=sub(proj, ":", "_")
   File bbm_bam
   File covstats
   File out_json
   File top100
   File out_json2
   File stats_json
   File stats_tsv
   String outdir
   String qadir="${outdir}/qa/"
   String assemdir="${outdir}/assembly/"
   String annodir="${outdir}/annotation/"
   String mapback="${outdir}/mapback/"
   String metat_out="${outdir}/metat_output/"
   File structural_gff
   File functional_gff
   File ko_tsv
   File ec_tsv
   File proteins_faa
   File ko_ec_gff
   File cog_gff
   File pfam_gff
   File tigrfam_gff
   File smart_gff
   File supfam_gff
   File cath_funfam_gff
   File cog_domtblout
   File pfam_domtblout
   File tigrfam_domtblout
   File smart_domtblout
   File supfam_domtblout
   File cath_funfam_domtblout
   File product_names_tsv
   File gene_phylogeny_tsv
   File crt_crisprs
   File crt_gff
   File genemark_gff
   File prodigal_gff
   File trna_gff
   File misc_bind_misc_feature_regulatory_gff
   File rrna_gff
   File ncrna_tmrna_gff
   File sorted_features
   String orig_prefix="scaffold"
   String sed="s/${orig_prefix}_/${proj}_/g"  


   command{
      set -e
      mkdir -p ${qadir}
      mkdir -p ${assemdir}
      mkdir -p ${mapback}
      mkdir -p ${annodir}
      mkdir -p ${metat_out}
      end=`date --iso-8601=seconds`


       #copy and re-ed qa objects
       cp ${filtered} ${qadir}/${prefix}_filtered.fastq.gz
       cp ${filtered_stats} ${qadir}/${prefix}_filterStats.txt
       cp ${filtered_stats2} ${qadir}/${prefix}_filterStats2.txt	
      
       # Generate QA objects
       /scripts/rqcstats.py ${filtered_stats} > stats.json
       cp stats.json ${qadir}/${prefix}_qa_stats.json

#       /scripts/generate_objects.py --type "nmdc:ReadQCAnalysisActivity" --id ${informed_by} \
#             --name "Read QC Activity for ${proj}" --part ${proj} \
#             --start ${start} --end $end \
#             --resource '${resource}' --url ${url_root}${proj}/qa/ --giturl ${git_url} \
#             --extra stats.json \
#             --inputs ${read} \
#             --outputs \
#             ${qadir}/${prefix}_filtered.fastq.gz 'Filtered Reads' \
#             ${qadir}/${prefix}_filterStats.txt 'Filtered Stats'
#       cp activity.json data_objects.json ${qadir}/

       #rename fasta
       cat ${fasta} | sed ${sed} > ${assemdir}/${prefix}_contigs.fna
       # Generate assembly objects
#       /scripts/generate_objects.py --type "nmdc:MetatranscriptomeAssembly" --id ${informed_by} \
#             --name "Assembly Activity for ${proj}" --part ${proj} \
#             --start ${start} --end $end \
#             --resource '${resource}' --url ${url_root}${proj}/assembly/ --giturl ${git_url} \
#             --extra stats.json \
#             --inputs ${qadir}/${prefix}_filtered.fastq.gz \
#             --outputs \
#             ${assemdir}/${prefix}_contigs.fna 'Assembled contigs fasta'
#       cp activity.json data_objects.json ${assemdir}/

       #rename mapping objects
       cat ${covstats} | sed ${sed} > ${mapback}/${prefix}_covstats.txt
       ## Bam file     
       samtools view -h ${bbm_bam} | sed ${sed} | \
          samtools view -hb -o ${mapback}/${prefix}_pairedMapped_sorted.bam
       # Generate mapping objects
#       /scripts/generate_objects.py --type "nmdc:MetatranscriptomeMapping" --id ${informed_by} \
#             --start ${start} --end $end \
#             --resource '${resource}' --url ${url_root}${proj}/mapback/ --giturl ${git_url} \
#             --inputs ${fasta} \
#             --outputs \
#             ${mapback}/${prefix}_pairedMapped_sorted.bam 'Mapping file' \
#	     ${mapback}/${prefix}_covstats.txt 'Metatranscriptome Contig Coverage Stats'
#       cp activity.json data_objects.json ${mapback}/

       # Generate annotation objects

       cat ${proteins_faa} | sed ${sed} > ${annodir}/${prefix}_proteins.faa
       cat ${structural_gff} | sed ${sed} > ${annodir}/${prefix}_structural_annotation.gff
       cat ${functional_gff} | sed ${sed} > ${annodir}/${prefix}_functional_annotation.gff
       cat ${ko_tsv} | sed ${sed} > ${annodir}/${prefix}_ko.tsv
       cat ${ec_tsv} | sed ${sed} > ${annodir}/${prefix}_ec.tsv
       cat ${cog_gff} | sed ${sed} > ${annodir}/${prefix}_cog.gff
       cat ${pfam_gff} | sed ${sed} > ${annodir}/${prefix}_pfam.gff
       cat ${tigrfam_gff} | sed ${sed} > ${annodir}/${prefix}_tigrfam.gff
       cat ${smart_gff} | sed ${sed} > ${annodir}/${prefix}_smart.gff
       cat ${supfam_gff} | sed ${sed} > ${annodir}/${prefix}_supfam.gff
       cat ${cath_funfam_gff} | sed ${sed} > ${annodir}/${prefix}_cath_funfam.gff
       cat ${crt_gff} | sed ${sed} > ${annodir}/${prefix}_crt.gff
       cat ${genemark_gff} | sed ${sed} > ${annodir}/${prefix}_genemark.gff
       cat ${prodigal_gff} | sed ${sed} > ${annodir}/${prefix}_prodigal.gff
       cat ${trna_gff} | sed ${sed} > ${annodir}/${prefix}_trna.gff
       cat ${misc_bind_misc_feature_regulatory_gff} | sed ${sed} > ${annodir}/${prefix}_rfam_misc_bind_misc_feature_regulatory.gff
       cat ${rrna_gff} | sed ${sed} > ${annodir}/${prefix}_rfam_rrna.gff
       cat ${ncrna_tmrna_gff} | sed ${sed} > ${annodir}/${prefix}_rfam_ncrna_tmrna.gff
       cat ${crt_crisprs} | sed ${sed} > ${annodir}/${prefix}_crt.crisprs
       cat ${product_names_tsv} | sed ${sed} > ${annodir}/${prefix}_product_names.tsv
       cat ${gene_phylogeny_tsv} | sed ${sed} > ${annodir}/${prefix}_gene_phylogeny.tsv

       cat ${ko_ec_gff} | sed ${sed} > ${annodir}/${prefix}_ko_ec.gff
       cat ${stats_tsv} | sed ${sed} > ${annodir}/${prefix}_stats.tsv
       cat ${stats_json} | sed ${sed} > ${annodir}/${prefix}_stats.json


#       /scripts/generate_objects.py --type "nmdc:MetatranscriptomeAnnotationActivity" --id ${informed_by} \
#             --name "Annotation Activity for ${proj}" --part ${proj} \
#             --start ${start} --end $end \
#             --resource '${resource}' --url ${url_root}${proj}/annotation/ --giturl ${git_url} \
#             --inputs ${assemdir}/${prefix}_contigs.fna \
#             --outputs \
#             ${annodir}/${prefix}_proteins.faa 'Protein FAA' \
#             ${annodir}/${prefix}_structural_annotation.gff 'Structural annotation GFF file' \
#             ${annodir}/${prefix}_functional_annotation.gff 'Functional annotation GFF file' \
#             ${annodir}/${prefix}_ko.tsv 'KO TSV file' \
#             ${annodir}/${prefix}_ec.tsv 'EC TSV file' \
#             ${annodir}/${prefix}_cog.gff 'COG GFF file' \
#             ${annodir}/${prefix}_pfam.gff 'PFAM GFF file' \
#             ${annodir}/${prefix}_tigrfam.gff 'TigrFam GFF file' \
#             ${annodir}/${prefix}_smart.gff 'SMART GFF file' \
#             ${annodir}/${prefix}_supfam.gff 'SuperFam GFF file' \
#             ${annodir}/${prefix}_cath_funfam.gff 'Cath FunFam GFF file' \
#             ${annodir}/${prefix}_crt.gff 'CRT GFF file' \
#             ${annodir}/${prefix}_genemark.gff 'Genemark GFF file' \
#             ${annodir}/${prefix}_prodigal.gff 'Prodigal GFF file' \
#             ${annodir}/${prefix}_trna.gff 'tRNA GFF File' \
#             ${annodir}/${prefix}_rfam_misc_bind_misc_feature_regulatory.gff 'RFAM misc binding GFF file' \
#             ${annodir}/${prefix}_rfam_rrna.gff 'RFAM rRNA GFF file' \
#            ${annodir}/${prefix}_rfam_ncrna_tmrna.gff 'RFAM rmRNA GFF file' \
#	     ${annodir}/${prefix}_crt.crisprs 'CRISPRS file' \
#	     ${annodir}/${prefix}_product_names.tsv 'Product Names tsv' \
#             ${annodir}/${prefix}_gene_phylogeny.tsv 'Gene Phylogeny tsv' \
#	     ${annodir}/${prefix}_ko_ec.gff 'KO_EC GFF file'
 #      cp features.json annotations.json activity.json data_objects.json ${annodir}/


       #re-id metat objects
       cat ${out_json} | sed ${sed} > ${metat_out}/${prefix}_sense_counts.json
       cat ${out_json2} | sed ${sed} > ${metat_out}/${prefix}_antisense_counts.json
       cat ${sorted_features} | sed ${sed} > ${metat_out}/${prefix}_sorted_features.tsv
       cat ${top100} | sed ${sed} > ${metat_out}/top100_features.json
       # Generate metat objects
#       /scripts/generate_objects.py --type "nmdc:MetatranscriptomeActivity" --id ${informed_by} \
#             --name "Metatranscriptome Activity for ${proj}"
#             --start ${start} --end $end \
#             --resource '${resource}' --url ${url_root}${proj}/metat_output/ --giturl ${git_url} \
#             --inputs ${functional_gff} ${bbm_bam}  \
#             --outputs \
#              ${metat_out}/${prefix}_sense_counts.json 'Sense RPKM' \
#              ${metat_out}/${prefix}_antisense_counts.json 'Anstisense RPKM' \
#	      ${metat_out}/${prefix}_sorted_features.tsv 'Sorted Features tsv'
  
#      cp activity.json data_objects.json ${metat_out}/

   }

   runtime {
     memory: "10 GiB"
     cpu:  4
     maxRetries: 1
     docker: container
   }
}
