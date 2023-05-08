task convtojson{
	File gff_file_path
	File gff_db_fn
	File fasta_file_name
	File pkm_sc_fn
	File rd_count_fn
	String name_of_feat
	String DOCKER
	File py_pack_path="pyp_metat"

	command <<<
		cp -R ${py_pack_path} pyp_metat
		python <<CODE
		from pyp_metat.to_json import ConverToJson
		json_conv_class = ConverToJson(gff_file_name="${gff_file_path}", gff_db_fn="${gff_db_fn}", fasta_file_name="${fasta_file_name}", pkm_sc_fn="${pkm_sc_fn}", rd_count_fn="${rd_count_fn}", name_of_feat="${name_of_feat}", out_json_file="${name_of_feat}.json")
		json_conv_class.gff2json()
		CODE
	>>>

	output{
		File out_json_file = "${name_of_feat}.json"
	}

	runtime {
		docker: DOCKER
	}
}

task dock_gtftojson{
	File gtf_file_name
	String name_of_feat
	String DOCKER

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
		json_conv_class = GTFtoJSON(gtf_file_name="${gtf_file_name}", name_of_feat="${name_of_feat}", out_json_file="${name_of_feat}.json")
		json_conv_class.gtf_json()
		CODE
	>>>

	output{
		File out_json_file = "${name_of_feat}.json"
	}

	runtime {
		docker: DOCKER
	}
}
