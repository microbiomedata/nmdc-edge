version 1.0

task stage {
   input{
      String container
      String proj
      String prefix=sub(proj, ":", "_")
      String target="~{prefix}.fastq.gz"
      String input_file
   }
   command <<<
       set -eou pipefail
       if [ $( echo ~{input_file}|egrep -c "https*:") -gt 0 ] ; then
           wget ~{input_file} -O ~{target}
       else
           cp ~{input_file} ~{target}
       fi
       date --iso-8601=seconds > start.txt
   >>>

   output{
      File read = "~{target}"
      String start = read_string("start.txt")
      String pref = "~{prefix}"
   }
   runtime {
     memory: "1 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }
}

task make_interleaved {
   input{
      File? fastq1
      File? fastq2
      String pref
      String container
   }
   command <<<
      set -eou pipefail
      reformat.sh in1=~{fastq1} in2=~{fastq2} out="~{pref}.fastq.gz"
   >>>

   output{
      File out_fastq = "~{pref}.fastq.gz"
   }
   runtime {
     memory: "1 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }
}

task split_interleaved_fastq{
    input{
      File reads
      String container
      String memory = "4G"
      String output1 = "input.left.fastq.gz"
      String output2 = "input.right.fastq.gz"
   }
    runtime {
        docker: container
        memory: "4 GiB"
        cpu:  1
    }
    command <<<
         set -eou pipefail
         reformat.sh -Xmx~{default="10G" memory} in=~{reads} out1=~{output1} out2=~{output2}
    >>>

    output {
            Array[File] outFastq = [output1, output2]
    }
}

task split_fastq{
   input{
      File intleave_fq_fl
   }

   command <<<
      set -eou pipefail
      cat ~{intleave_fq_fl} | paste - - - - - - - - | tee | cut -f 1-4 | tr "\t" "\n" | egrep -v '^$' > R1.fastq
      cat ~{intleave_fq_fl} | paste - - - - - - - - | tee | cut -f 5-8 | tr "\t" "\n" | egrep -v '^$' > R2.fastq

   >>>

   output{
      File out_r1_file = "R1.fastq"
      File out_r2_file = "R2.fastq"
   }
}

task clean_gff{
   input{
      File gff_file_path
      String DOCKER
   }
   command <<<
      set -eou pipefail
    # removing special characters that featurecount didnt like when parsing gff
      sed "s/\'//g" ~{gff_file_path} | sed "s/-/_/g"  > clean.gff

   >>>

   output{
      File cln_gff_fl = "clean.gff"
   }

   runtime {
      docker: DOCKER
      memory: "1 GiB"
      cpu:  1
   }
}

task extract_feats{
   input{
      File gff_file_path
      String DOCKER
   }
   command <<<
      set -eou pipefail
      awk -F'\t' '{print $3}' ~{gff_file_path} | sort | uniq
   >>>

   output{
      Array[String] feats_in_gff = read_lines(stdout())
   }

   runtime {
      docker: DOCKER
      memory: "1 GiB"
      cpu:  1
   }
}

task create_gffdb{
   input {
      File gff_file_path
      String DOCKER
   }
   command <<<
      set -eou pipefail
      python <<CODE
      import gffutils
      gffutils.create_db("~{gff_file_path}", dbfn="gff.db", force=True, keep_order=True, merge_strategy="create_unique")
      CODE
   >>>

   output{
      File gff_db_fn = "gff.db"
   }
   runtime {
      docker: DOCKER
      memory: "1 GiB"
      cpu:  1
   }
}

task collect_output{
   input {
      Array[File] out_files
      String prefix
      String DOCKER
   }
   command <<<
      set -eou pipefail
      python <<OEF
      import json
      out_file = "~{prefix}" + "_sense_out.json"
      result = []
      list_of_fls = ['~{sep="','" out_files}']
      for f in list_of_fls:
         with open(f, "rb") as infile:
            result.append(json.load(infile))
      with open(out_file, "w") as outfile:
         json.dump(result, outfile, indent=4)
      OEF
   >>>

   runtime {
      docker: DOCKER
      memory: "1 GiB"
      cpu:  1
   }

   output{
      File out_json_file = prefix + "_sense_out.json"
   }
}

task collect_output2{
   input{
        Array[File] out_files
        String prefix
        String DOCKER
   }
      command <<<

         set -eou pipefail
         python <<CODE
         import json
         out_file = "~{prefix}" + "_antisense_out.json"
         result = []
         list_of_fls = ['~{sep="','" out_files}']
         for f in list_of_fls:
               with open(f, "rb") as infile:
                        result.append(json.load(infile))
         with open(out_file, "w") as outfile:
               json.dump(result, outfile, indent=4)
         CODE
        >>>

        runtime {
            docker: DOCKER
            memory: "1 GiB"
            cpu:  1
        }

        output{
                File out_json_file2 = prefix + "_antisense_out.json"
        }
}

task rctojson{
   input {
      File gff
      File readcount
      String prefix
      String container
   }
   command <<<
        python <<CODE
        # Imports #######################################################################################################################################
        import os
        import json
        import pandas as pd
        import gffutils
        # Definitions #####################################################################################################################################
        # Functions #######################################################################################################################################
        def final_jsons(gff_in = "test_data/paired.gff", rc_in = "test_data/paired.rc", 
                    gff_json = "paired.gff.json", 
                    rc_json = "paired.rc.json",
                    gff_rc_json = "gff_rc.json",
                    cds_json = "cds_counts.json",
                    sense_json = "sense_counts.json",
                    anti_json = "antisense_counts.json",
                    sorted_json = "sorted_features.json",
                    sorted_tsv = "sorted_features.tsv",
                    top100_json = "top100_features.json",
                    prefix = ""
                    ):
            """
            Generate JSON files for NMDC EDGE MetaT output tables. 
            Combine JSON files from GFF and read count TSV using pandas
            """
            if (prefix != ""):
                gff_json = prefix + "_paired.gff.json"
                rc_json = prefix + "_paired.rc.json"
                gff_rc_json = prefix + "_gff_rc.json"
                cds_json = prefix + "_cds_counts.json"
                sense_json = prefix + "_sense_counts.json"
                anti_json = prefix + "_antisense_counts.json"
                sorted_json = prefix + "_sorted_features.json"
                sorted_tsv = prefix + "_sorted_features.tsv"
                top100_json = prefix + "_top100_features.json"
            
            gff_obj = GTFtoJSON(gff_in, gff_json).gtf_json()
            
            rc_obj = TSVtoJSON(rc_in, rc_json).tsv_json()

            gff_pd1 = pd.read_json(gff_json)
            rc_pd1 = pd.read_json(rc_json)

            gff_pd = gff_pd1.fillna(value = "NA")
            rc_pd = rc_pd1.fillna(value = "NA")
            print("NaN filled")

            gff_rc_pd = pd.merge(gff_pd, rc_pd, on = ["id", "seqid", "featuretype", "strand", "length"])

            cds_only = gff_rc_pd[gff_rc_pd['featuretype'] == "CDS"]

            sense_reads = cds_only[cds_only['strand'] == "+"].drop(columns = ["antisense_read_count", 
                                    "meanA",
                                    "medianA",
                                    "stdevA"])
            antisense_reads = cds_only[cds_only['strand'] == "-"].drop(columns = ["sense_read_count", 
                                    "mean",
                                    "median",
                                    "stdev"])

            sorted_features = gff_rc_pd.sort_values(by='sense_read_count', ascending=False)
            top100 = sorted_features[:100]
            
            gff_rc_pd.to_json(orient="records", path_or_buf = gff_rc_json, indent = 4)
            cds_only.to_json(orient="records", path_or_buf = cds_json, indent = 4)
            sense_reads.to_json(orient="records", path_or_buf = sense_json, indent = 4)
            antisense_reads.to_json(orient="records", path_or_buf = anti_json, indent = 4)
            sorted_features.to_json(orient="records", path_or_buf =  sorted_json, indent = 4)
            top100.to_json(orient="records", path_or_buf =  top100_json, indent = 4)
            
            sorted_features.to_csv(sorted_tsv, sep="\t") 
            
            print("Additional JSON files and tables printed.")



        # Classes #######################################################################################################################################
        class GTFtoJSON():
            """
            Converts GTF files to JSON records.

            Utilizes package gffutils to create database from gff / gtf files in gtf_json()
            Extracts desired attributes and features to json using collect_features().
            Utilizes package json to write json out and package os to check for db existence. 
            """

            def __init__(self, gtf_file_name: str, out_json_file: str):
                """
                gtf_file_name: string of gtf or gff file, relative or absolute path both work
                out_json_file: name of desired json output file, relative or absolute
                """
                self.gtf_file_name = gtf_file_name
                self.out_json_file = out_json_file

            def gtf_json(self):
                """
                A function that converts a gff file to JSON file.
                Reads gff in and exports to db (SQL) type file.
                Uses db type format to channel to collect_features and extract attributes to dictionary before writing to json.
                """
                # read in the gff file to a database
                if os.path.exists("metat_db.db") is False:
                    gtf_as_db = gffutils.create_db(self.gtf_file_name, dbfn="metat_db.db", force=True,
                                        keep_order=True,
                                        merge_strategy="create_unique")
                    print("New gffutils db created")
                else:
                    gtf_as_db = gffutils.FeatureDB("metat_db.db", keep_order=True)
                    print("Cached gffutils db loaded")
                json_list = []
                for feat_obj in gtf_as_db.all_features():
                    feat_dic_str = self.collect_features(feat_obj=feat_obj)
                    if bool(feat_dic_str):  # only append if dic is not empty
                        json_list.append(feat_dic_str)

                with open(self.out_json_file, "w") as out_json:
                    json.dump(json_list, out_json, indent=4)

                print("GTF to JSON completed")
                return json_list
                

            def collect_features(self, feat_obj):
                """
                A function that collect features. Usually called via gtf_json()
                feat_obj is each object give through loop of db from gffutils
                """
                feat_dic = {}
                feat_dic['featuretype'] = feat_obj.featuretype
                feat_dic['seqid'] = feat_obj.seqid
                feat_dic['id'] = feat_obj.id
                feat_dic['source'] = feat_obj.source
                feat_dic['start'] = feat_obj.start
                feat_dic['end'] = feat_obj.end
                feat_dic['length'] = abs(feat_obj.end - feat_obj.start) + 1
                feat_dic['strand'] = feat_obj.strand
                feat_dic['frame'] = feat_obj.frame
                try:
                    feat_dic['product'] = feat_obj.attributes['product'][0]
                    feat_dic['product_source'] = feat_obj.attributes['product_source'][0]
                except KeyError:
                    pass
                try:
                    feat_dic['cov'] = feat_obj.attributes['cov'][0]
                except KeyError:
                    pass
                try:
                    feat_dic['FPKM'] = feat_obj.attributes['FPKM'][0]
                except KeyError:
                    pass
                try:
                    feat_dic['TPM'] = feat_obj.attributes['TPM'][0]
                except KeyError:
                    pass

                return feat_dic

        ########################################################################################################################################

        class TSVtoJSON():
            """ 
            Convert TSV output from JGI ReadCounts script to JSON format 
            to combine with functional annotation gff file
            feat_dic['sense_read_count'] = DY's reads_cnt
            
            """
            def __init__(self, tsv_file_name: str, out_json_file: str):
                self.tsv_file_name = tsv_file_name
                self.out_json_file = out_json_file
            
            def tsv_json(self):
                """
                Convert TSV to dictionaries for writing out to json
                Uses pandas to read in CSV, rename columns, drop empty column, and create dictionary for json dumping. 
                """
                tsv_obj = pd.read_csv(
                    self.tsv_file_name, sep="\t"
                    ).drop(columns = ["locus_tag", "scaffold_accession"]
                    ).rename(columns = {"img_gene_oid": "id", 
                                    "img_scaffold_oid": "seqid",
                                    "reads_cnt": "sense_read_count",
                                    "reads_cntA": "antisense_read_count",
                                    "locus_type": "featuretype"})

                tsv_obj.to_json(orient="records", path_or_buf = self.out_json_file, indent = 4)
                
                print("TSV to JSON completed")
        # Function call #######################################################################################################################################
        final_jsons(gff_in = "~{gff}", rc_in = "~{readcount}", prefix = "~{prefix}")
        ########################################################################################################################################
        CODE
    >>>

   output{
      File gff_json = "~{prefix}_paired.gff.json"
      File rc_json = "~{prefix}_paired.rc.json"
      File gff_rc_json = "~{prefix}_gff_rc.json"
      File cds_json = "~{prefix}_cds_counts.json"
      File sense_json = "~{prefix}_sense_counts.json"
      File anti_json = "~{prefix}_antisense_counts.json"
      File top100_json = "~{prefix}_top100_features.json"
      File sorted_json = "~{prefix}_sorted_features.json"
      File sorted_tsv = "~{prefix}_sorted_features.tsv"
   }

   runtime {
     memory: "8 GiB"
     cpu:  2
     maxRetries: 1
     docker: container
   }

}

task finish_metat {
   input{
      String container
      String proj
      String prefix=sub(proj, ":", "_")
      String outdir = "Metatranscriptomics/"
      String qcdir="~{outdir}/readsQC/"
      String assemdir="~{outdir}/assembly/"
      String annodir="~{outdir}/annotation/"
      String readmap="~{outdir}/readMapping/"
      # metaT_ReadsQC
      File filtered 
      File filtered_stats
      File filtered_stats2
      File rqc_info
      # metaT_Assembly
      File tar_bam 
      File contigs
      File scaffolds 
      File readlen 
      File sam 
      File bam 
      File asmstats 
      File asse_info  
      File asse_log
      # mg_annotation
      File proteins_faa 
      File structural_gff 
      File ko_ec_gff
      File gene_phylogeny_tsv 
      File functional_gff 
      File ko_tsv 
      File ec_tsv 
      File lineage_tsv 
      File stats_tsv 
      File cog_gff 
      File pfam_gff 
      File tigrfam_gff 
      File smart_gff 
      File supfam_gff 
      File cath_funfam_gff 
      File crt_gff
      File genemark_gff
      File prodigal_gff
      File trna_gff
      File rfam_gff
      File product_names_tsv
      File crt_crisprs
      File imgap_version
      File renamed_fasta 
      File map_file 
      # metaT_ReadCounts
      File count_table
      File? count_ig
      File? count_log 
      File readcount_info 
      # output tables
      File gff_json
      File rc_json 
      File gff_rc_json 
      File cds_json 
      File sense_json 
      File anti_json 
      File top100_json 
      File sorted_json 
      File sorted_tsv 
   }

   command <<<
      set -eou pipefail
      mkdir -p ~{qcdir}
      mkdir -p ~{assemdir}
      mkdir -p ~{readmap}
      mkdir -p ~{annodir}
      end=`date --iso-8601=seconds`

      #move qc objects
      cp ~{filtered} ~{qcdir}/~{prefix}_filtered.fastq.gz
      cp ~{filtered_stats} ~{qcdir}/~{prefix}_filterStats.txt
      cp ~{filtered_stats2} ~{qcdir}/~{prefix}_filterStats2.txt	
      cp ~{rqc_info} ~{qcdir}/~{prefix}_rqc.info	
      # Generate QC objects
      /scripts/rqcstats.py ~{filtered_stats} > stats.json
      cp stats.json ~{qcdir}/~{prefix}_qc_stats.json 

      # move assy objects
      cp ~{tar_bam} ~{assemdir}/~{prefix}_bamfiles.tar
      cp ~{contigs} ~{assemdir}/~{prefix}_contigs.fna
      cp ~{scaffolds} ~{assemdir}/~{prefix}_scaffolds.fna
      cp ~{readlen} ~{assemdir}/~{prefix}_readlen.txt
      cp ~{sam} ~{assemdir}/~{prefix}_pairedMapped.sam.gz
      cp ~{bam} ~{assemdir}/~{prefix}_pairedMapped.bam.gz
      cp ~{asmstats} ~{assemdir}/~{prefix}_scaffold_stats.json 
      cp ~{asse_info} ~{assemdir}/~{prefix}_assy.info 
      cp ~{asse_log} ~{assemdir}/~{prefix}_spades.log

      # move anno objects
      cp ~{proteins_faa} ~{annodir}/~{prefix}_proteins.faa
      cp ~{structural_gff} ~{annodir}/~{prefix}_structural_annotation.gff
      cp ~{ko_ec_gff} ~{annodir}/~{prefix}_ko_ec.gff
      cp ~{gene_phylogeny_tsv} ~{annodir}/~{prefix}_gene_phylogeny.tsv
      cp ~{functional_gff} ~{annodir}/~{prefix}_functional_annotation.gff
      cp ~{ko_tsv} ~{annodir}/~{prefix}_ko.tsv
      cp ~{ec_tsv} ~{annodir}/~{prefix}_ec.tsv
      cp ~{lineage_tsv} ~{annodir}/~{prefix}_scaffold_lineage.tsv
      cp ~{stats_tsv} ~{annodir}/~{prefix}_anno_stats.tsv
      cp ~{cog_gff} ~{annodir}/~{prefix}_cog.gff
      cp ~{pfam_gff} ~{annodir}/~{prefix}_pfam.gff
      cp ~{tigrfam_gff} ~{annodir}/~{prefix}_tigrfam.gff
      cp ~{smart_gff} ~{annodir}/~{prefix}_smart.gff
      cp ~{supfam_gff} ~{annodir}/~{prefix}_supfam.gff
      cp ~{cath_funfam_gff} ~{annodir}/~{prefix}_cath_funfam.gff
      cp ~{crt_gff} ~{annodir}/~{prefix}_crt.gff
      cp ~{genemark_gff} ~{annodir}/~{prefix}_genemark.gff
      cp ~{prodigal_gff} ~{annodir}/~{prefix}_prodigal.gff
      cp ~{trna_gff} ~{annodir}/~{prefix}_trna.gff
      cp ~{rfam_gff} ~{annodir}/~{prefix}_rfam.gff
      cp ~{product_names_tsv} ~{annodir}/~{prefix}_product_names.tsv
      cp ~{crt_crisprs} ~{annodir}/~{prefix}_crt.crisprs
      cp ~{imgap_version} ~{annodir}/~{prefix}_anno.info
      cp ~{renamed_fasta} ~{annodir}/~{prefix}_renamed_contigs.fna
      cp ~{map_file} ~{annodir}/~{prefix}_map.fna

      # move readcount objects
      cp ~{count_table} ~{readmap}/~{prefix}.readcount
      cp ~{count_ig} ~{readmap}/~{prefix}.readcount.intergenic
      cp ~{count_log} ~{readmap}/~{prefix}.readcount.Stats.log
      cp ~{readcount_info} ~{readmap}/~{prefix}_readcount.info

      #move metat tables
      cp ~{gff_json} ~{readmap}/~{prefix}_paired.gff.json
      cp ~{rc_json} ~{readmap}/~{prefix}_paired.rc.json
      cp ~{gff_rc_json} ~{readmap}/~{prefix}_gff_rc.json
      cp ~{cds_json} ~{readmap}/~{prefix}_cds_counts.json
      cp ~{sense_json} ~{readmap}/~{prefix}_sense_counts.json
      cp ~{anti_json} ~{readmap}/~{prefix}_antisense_counts.json
      cp ~{top100_json} ~{readmap}/~{prefix}_top100_features.json
      cp ~{sorted_json} ~{readmap}/~{prefix}_sorted_features.json
      cp ~{sorted_tsv} ~{readmap}/~{prefix}_sorted_features.tsv


   >>>

      output {
         # metaT_ReadsQC
         File final_filtered = "~{qcdir}/~{prefix}_filtered.fastq.gz"
         File final_filtered_stats= "~{qcdir}/~{prefix}_filterStats.txt"
         File final_filtered_stats2 = "~{qcdir}/~{prefix}_filterStats2.txt"
         File final_rqc_info = "~{qcdir}/~{prefix}_rqc.info"
         File final_rqc_stats = "~{qcdir}/~{prefix}_qc_stats.json"

         # metaT_Assembly
         File final_tar_bam = "~{assemdir}/~{prefix}_bamfiles.tar"
         File final_contigs = "~{assemdir}/~{prefix}_contigs.fna"
         File final_scaffolds = "~{assemdir}/~{prefix}_scaffolds.fna"
         File final_readlen = "~{assemdir}/~{prefix}_readlen.txt"
         File final_sam = "~{assemdir}/~{prefix}_pairedMapped.sam.gz"
         File final_bam = "~{assemdir}/~{prefix}_pairedMapped.bam.gz"
         File final_asmstats = "~{assemdir}/~{prefix}_scaffold_stats.json"
         File final_asm_info = "~{assemdir}/~{prefix}_assy.info"
         File final_asm_log = "~{assemdir}/~{prefix}_spades.log"

         # mg_annotation
         File final_proteins_faa = "~{annodir}/~{prefix}_proteins.faa"
         File final_structural_gff = "~{annodir}/~{prefix}_structural_annotation.gff"
         File final_ko_ec_gff = "~{annodir}/~{prefix}_ko_ec.gff"
         File final_gene_phylogeny_tsv = "~{annodir}/~{prefix}_gene_phylogeny.tsv"
         File final_functional_gff = "~{annodir}/~{prefix}_functional_annotation.gff"
         File final_ko_tsv = "~{annodir}/~{prefix}_ko.tsv"
         File final_ec_tsv = "~{annodir}/~{prefix}_ec.tsv"
         File final_lineage_tsv = "~{annodir}/~{prefix}_scaffold_lineage.tsv"
         File final_stats_tsv = "~{annodir}/~{prefix}_anno_stats.tsv"
         File final_cog_gff = "~{annodir}/~{prefix}_cog.gff"
         File final_pfam_gff = "~{annodir}/~{prefix}_pfam.gff"
         File final_tigrfam_gff = "~{annodir}/~{prefix}_tigrfam.gff"
         File final_smart_gff = "~{annodir}/~{prefix}_smart.gff"
         File final_supfam_gff = "~{annodir}/~{prefix}_supfam.gff"
         File final_cath_funfam_gff = "~{annodir}/~{prefix}_cath_funfam.gff"
         File final_crt_gff = "~{annodir}/~{prefix}_crt.gff"
         File final_genemark_gff = "~{annodir}/~{prefix}_genemark.gff"
         File final_prodigal_gff = "~{annodir}/~{prefix}_prodigal.gff"
         File final_trna_gff = "~{annodir}/~{prefix}_trna.gff"
         File final_rfam_gff = "~{annodir}/~{prefix}_rfam.gff"
         File final_product_names_tsv = "~{annodir}/~{prefix}_product_names.tsv"
         File final_crt_crisprs = "~{annodir}/~{prefix}_crt.crisprs"
         File final_imgap_version = "~{annodir}/~{prefix}_anno.info"
         File final_renamed_fasta = "~{annodir}/~{prefix}_renamed_contigs.fna"
         File final_map_file = "~{annodir}/~{prefix}_map.fna"

         # metaT_ReadCounts
         File final_count_table = "~{readmap}/~{prefix}.readcount"
         File? final_count_ig = "~{readmap}/~{prefix}.readcount.intergenic"
         File? final_count_log = "~{readmap}/~{prefix}.readcount.Stats.log"
         File final_readcount_info = "~{readmap}/~{prefix}_readcount.info"

         # re-id metat objects
         File final_gff_json = "~{readmap}/~{prefix}_paired.gff.json"
         File final_rc_json = "~{readmap}/~{prefix}_paired.rc.json"
         File final_gff_rc_json = "~{readmap}/~{prefix}_gff_rc.json"
         File final_cds_json = "~{readmap}/~{prefix}_cds_counts.json"
         File final_sense_json = "~{readmap}/~{prefix}_sense_counts.json"
         File final_anti_json = "~{readmap}/~{prefix}_antisense_counts.json"
         File final_top100_json = "~{readmap}/~{prefix}_top100_features.json"
         File final_sorted_json = "~{readmap}/~{prefix}_sorted_features.json"
         File final_sorted_tsv = "~{readmap}/~{prefix}_sorted_features.tsv"
      }


   runtime {
     memory: "10 GiB"
     cpu:  4
     maxRetries: 1
     docker: container
   }
}
