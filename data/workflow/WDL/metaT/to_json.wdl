version 1.0

workflow to_json {
    input {
        File gff
		File readcount
		String prefix
    }

    call rctojson{
        input:
        gff = gff,
        readcount = readcount,
        prefix = prefix
    }
}

task rctojson{
	input {
		File gff
		File readcount
		String prefix
		String container = "microbiomedata/meta_t@sha256:7e2f1566d3aa64ad55981c5e294b144b20889cbc6d6d24e54d364f379c782324"
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

			gff_pd = pd.read_json(gff_json)
			rc_pd = pd.read_json(rc_json)
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
			
			write_json(gff_rc_pd.to_dict(orient="records"), gff_rc_json)
			write_json(cds_only.to_dict(orient="records"), cds_json)
			write_json(sense_reads.to_dict(orient="records"), sense_json)
			write_json(antisense_reads.to_dict(orient="records"), anti_json)
			write_json(sorted_features.to_dict(orient="records"), sorted_json)
			write_json(top100.to_dict(orient="records"), top100_json)
			
			sorted_features.to_csv(sorted_tsv, sep="\t") 
			
			print("Additional JSON files and tables printed.")

			
		def write_json(js_data, file_out: str):
			with open(file_out, 'w') as json_file:
				json.dump(js_data, json_file, indent=4)

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
					feat_dic = {}  # an empty dictionary to append features
					feat_dic_str = self.collect_features(feat_obj=feat_obj, feat_dic=feat_dic)
					if bool(feat_dic_str):  # only append if dic is not empty
						json_list.append(feat_dic_str)

				write_json(json_list, self.out_json_file)
				print("GTF to JSON completed")
				return json_list
				

			def collect_features(self, feat_obj, feat_dic: dict):
				"""
				A function that collect features. Usually called via gtf_json()
				feat_obj is each object give through loop of db from gffutils
				"""
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
				# just to make sure that keys are strings, else json dump fails
				feat_dic_str = {}
				for key, value in feat_dic.items():
					feat_dic_str[str(key)] = value
				return feat_dic_str

		########################################################################################################################################

		class TSVtoJSON():
			""" 
			Convert TSV output from JGI ReadCounts script to JSON format 
			to combine with functional annotation gff file
			feat_dic['sense_read_count'] = DY's reads_cnt
			feat_dic['antisense_read_count'] = DY's reads_cntA instead of feat_dic['FPKM'] = feat_obj.attributes['FPKM']
			you will have to make it read the DY's output, ingest to a dic, read the functional annotation gff file using gffutils packages, and then add selected variables to the same dic and convert it to json and csv
				
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
				# tsv_dic = tsv_obj.to_dict(orient="records")
				print("TSV to JSON completed")

				write_json(tsv_obj.to_dict(orient="records"), self.out_json_file)
	
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
		docker: container
	}

}





task convtojson{
	input{
		File gff_file_path
		File gff_db_fn
		File fasta_file_name
		File pkm_sc_fn
		File rd_count_fn
		String name_of_feat
		String DOCKER
		File py_pack_path="pyp_metat"
	}

	command <<<
		cp -R ~{py_pack_path} pyp_metat
		python <<CODE
		from pyp_metat.to_json import ConverToJson
		json_conv_class = ConverToJson(gff_file_name="~{gff_file_path}", gff_db_fn="~{gff_db_fn}", fasta_file_name="~{fasta_file_name}", pkm_sc_fn="~{pkm_sc_fn}", rd_count_fn="~{rd_count_fn}", name_of_feat="~{name_of_feat}", out_json_file="~{name_of_feat}.json")
		json_conv_class.gff2json()
		CODE
	>>>

	output{
		File out_json_file = "~{name_of_feat}.json"
	}

	runtime {
		docker: DOCKER
	}
}

task dock_gtftojson{
	input {
		File gtf_file_name
		String name_of_feat
		String DOCKER
	}

	command <<<
		python <<CODE
		import os
		import json
		import pandas as pd
		import gffutils

		class GTFtoJSON():
			"""Converts GTF files to JSON records."""

			def __init__(self, gtf_file_name, name_of_feat, out_json_file):
				self.gtf_file_name = gtf_file_name
				self.name_of_feat = name_of_feat
				self.out_json_file = out_json_file

			def gtf_json(self):
				"""A function that converts a gff file to JSON file."""
				# read in the gff file to a database
				if os.path.exists("metat_db.db") is False:
					gtf_as_db = gffutils.create_db(self.gtf_file_name, dbfn="metat_db.db", force=True,
												keep_order=True,
												merge_strategy="create_unique")
				else:
					gtf_as_db = gffutils.FeatureDB("metat_db.db", keep_order=True)
				json_list = []
				with open(self.out_json_file, "w") as json_file:
					for feat_obj in gtf_as_db.all_features():
						feat_dic = {}  # an empty dictionary to append features
						feat_type = feat_obj.featuretype
						if feat_type == self.name_of_feat:
							feat_dic_str = self.collect_features(
								feat_type=feat_type, feat_obj=feat_obj, feat_dic=feat_dic)
							if bool(feat_dic_str):  # only append if dic is not empty
								json_list.append(feat_dic_str)
					json.dump(json_list, json_file, indent=4)

			def collect_features(self, feat_type, feat_obj, feat_dic):
				"""A function that collect features."""
				feat_dic['featuretype'] = feat_type
				feat_dic['seqid'] = feat_obj.seqid
				feat_dic['id'] = feat_obj.id
				feat_dic['source'] = feat_obj.source
				feat_dic['start'] = feat_obj.start
				feat_dic['end'] = feat_obj.end
				feat_dic["length"] = abs(feat_obj.end - feat_obj.start) + 1
				feat_dic['strand'] = feat_obj.strand
				feat_dic['frame'] = feat_obj.frame
				feat_dic['extra'] = feat_obj.extra
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
				# just to make sure that keys are strings, else json dump fails
				feat_dic_str = {}
				for key, value in feat_dic.items():
					feat_dic_str[str(key)] = value
				return feat_dic_str
		json_conv_class = GTFtoJSON(gtf_file_name="~{gtf_file_name}", name_of_feat="~{name_of_feat}", out_json_file="~{name_of_feat}.json")
		json_conv_class.gtf_json()
		CODE
	>>>

	output{
		File out_json_file = "~{name_of_feat}.json"
	}

	runtime {
		docker: DOCKER
	}
}
