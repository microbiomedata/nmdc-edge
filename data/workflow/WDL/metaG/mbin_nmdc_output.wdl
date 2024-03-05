workflow mbin_nmdc_output {
    String? outdir
    String  proj_name
    String start
    File contig_file
    File sam_file
    File gff_file
    File low
    File unbinned
    File short
    File checkm
    File json_stats
    File tsv_stats
    File bacsum
    File arcsum
    Array[File] bin_fasta_files
    Array[File] hqmq_bin_fasta_files
    String container = "microbiomedata/nmdc_mbin:0.1.6"
    String? proj = "MAGs"
    String? informed_by = "${proj}"  # "nmdc:xxxxxxxxxxxxxxx"
    String resource = "SDSC - Expanse"
    String url_root = "https://data.microbiomedata.org/data/"
    String git_url = "https://github.com/microbiomedata/metaMAGs/releases/tag/1.0.2"

  call generate_objects {
         input: container="microbiomedata/workflowmeta:1.0.5.1",
                proj = proj_name,
                start = start,
                informed_by = "${informed_by}",
                resource = "${resource}",
                url_base = "${url_root}",
                git_url = "${git_url}",
                fasta = "${contig_file}",
                bam = "${sam_file}",
                functional_gff ="${gff_file}",
                lowdepth = low,
                unbinned = unbinned,
                short = short,
                checkm = checkm,
                json_stats = json_stats,
                bac_summary = bacsum,
                ar_summary = arcsum,
                metabat_bin_fasta_files = bin_fasta_files,
                hqmq_bin_fasta_files = hqmq_bin_fasta_files
    }

  call make_output {
            input: container="microbiomedata/workflowmeta:1.0.5.1",
                   activity_json=generate_objects.activity_json,
                   object_json=generate_objects.data_object_json,
                   short=short,
                   low=low,
                   unbinned=unbinned,
                   json_stats=json_stats,
                   tsv_stats=tsv_stats,
                   hqmq_bin_fasta_zip=generate_objects.hqmq_bin_fasta_zip,
                   bin_fasta_zip=generate_objects.metabat_bin_fasta_zip,
                   checkm=checkm,
                   gtdbtk_bac_summary=bacsum,
                   gtdbtk_ar_summary=arcsum,
                   proj = proj_name,
                   outdir=outdir

        }
}
task generate_objects{
    String container
    String start
    String proj
    String informed_by
    String resource
    String url_base
    String git_url
    File fasta
    File bam
    File? checkm
    File functional_gff
    File short
    File lowdepth
    File unbinned
    File json_stats

    File? bac_summary
    File? ar_summary
    Array[File] metabat_bin_fasta_files
    Array[File] hqmq_bin_fasta_files
    String dollar="$"

    command<<<
        set -e
        end=`date --iso-8601=seconds`
        ### set IFS to avoid space separate string and save into the outputs array elements
        IFS=""
        outputs=()
        zip -j hqmq-metabat-bins.zip ${sep=" " hqmq_bin_fasta_files} || true
        zip -j metabat-bins.zip ${sep=" " metabat_bin_fasta_files} || true
        [ -e hqmq-metabat-bins.zip ] && outputs+=( "hqmq-metabat-bins.zip" ) && outputs+=( "high quality and medium quality bin fasta output" )
        [ -e maetabat-bins.zip ] && outputs+=( "metabat-bins.zip" ) && outputs+=( "initial metabat bining result fasta output" )

        /scripts/generate_objects.py --type "MAGs" --id ${informed_by} \
	     --name "MAGs Analysis Activity for ${proj}" --part ${proj} \
             --start ${start} --end $end \
             --extra ${json_stats} \
             --resource '${resource}' --url ${url_base} --giturl ${git_url} \
             --inputs ${fasta} ${bam} ${functional_gff} \
             --outputs ${dollar}{outputs[@]} \
             ${short} "tooShort (< 3kb) filtered contigs fasta file by metaBat2" \
             ${lowdepth} "lowDepth (mean cov <1 )  filtered contigs fasta file by metabat2" \
             ${unbinned} "unbinned fasta file from metabat2" \
             ${" " + checkm + " \"metabat2 bin checkm quality assessment result\""} \
             ${" " + bac_summary + " \"gtdbtk bacterial assignment result summary table\""} \
             ${" " + ar_summary + " \"gtdbtk archaea assignment result summary table\""}
    >>>
    runtime {
        docker: container
        memory: "10 GiB"
        cpu:  1
    }
    output{
        File activity_json = "activity.json"
        File data_object_json = "data_objects.json"
        File? metabat_bin_fasta_zip = "hqmq-metabat-bins.zip"
        File? hqmq_bin_fasta_zip = "metabat-bins.zip"
    }
}


task make_output{
    String outdir
    File short
    File low
    File unbinned
    String proj
    File? hqmq_bin_fasta_zip
    File? bin_fasta_zip
    File? checkm
    File json_stats
    File tsv_stats
    File? gtdbtk_bac_summary
    File? gtdbtk_ar_summary
    String container
    File activity_json
    File object_json
    String sed_bin="s/bins./${proj}_/g"

    command <<<
        mkdir -p ${outdir}
        cp ${activity_json} ${object_json} ${outdir}
        cp ${low}  ${outdir}/${proj}_bins.lowDepth.fa
        cp ${short} ${outdir}/${proj}_bins.tooShort.fa
        cp ${unbinned} ${outdir}/${proj}_bins.unbinned.fa
        cp ${checkm} ${outdir}/${proj}_checkm_qa.out
        sed -i ${sed_bin} ${outdir}/${proj}_checkm_qa.out
        sed -e ${sed_bin} ${json_stats} > ${outdir}/MAGs_stats.json
        sed -e ${sed_bin} ${tsv_stats} > ${outdir}/mbin_datafile_${proj}.txt
        sed -e ${sed_bin} ${gtdbtk_bac_summary} > ${outdir}/gtdbtk.bac120.summary.tsv
        sed -e ${sed_bin} ${gtdbtk_ar_summary} > ${outdir}/gtdbtk.ar122.summary.tsv
        # These may not exist
        ${  if defined(bin_fasta_zip) then
                 "cp " + bin_fasta_zip + " " + outdir + "/"  + proj + "_metabat_bins.zip"
            else
                 "mkdir -p meta && cd meta && touch no_mags.txt && zip " + outdir + "/" + proj + "_metabat_bins.zip *.txt"
        }
        ${  if defined(hqmq_bin_fasta_zip) then
                 "cp " + hqmq_bin_fasta_zip + " " + outdir + "/"  + proj + "_hqmq_bins.zip"
            else
                 "mkdir -p hqmq && cd hqmq && touch no_hqmq_mags.txt && zip " + outdir + "/" + proj + "_hqmq_bins.zip *.txt"
        }
        chmod 755 -R ${outdir}
    >>>
    output {
        File? hqmq_bin_fa_zip = "${outdir}/$(proj)_hqmq_bins.zip"
        File? metabat_bin_fa_zip = "${outdir}/${proj}_metabat_bins.zip"
        File? checkm_output = "${outdir}/${proj}_checkm_qa.out"
        File? bac_summary = "${outdir}/gtdbtk.bac120.summary.tsv"
        File? ar_summary = "${outdir}/gtdbtk.ar122.summary.tsv"
        File? unbinned_fa = "${outdir}/${proj}_bins.unbinned.fa"
        File? tooShort_fa = "${outdir}/${proj}_bins.tooShort.fa"
        File? lowDepth_fa = "${outdir}/${proj}_bins.lowDepth.fa"
        File? tsvstats = "${outdir}/mbin_datafile_${proj}.txt"
        File? stats = "${outdir}/MAGs_stats.json"
        File? outactivity = "${outdir}/activity.json"
        File? outobject = "${outdir}/data_objects.json"
    }
    runtime {
        docker: container
        memory: "1 GiB"
        cpu:  1
    }
}
