workflow jgi_metaASM {
    Array[File] input_file
    String? outdir
    String? memory
    String? threads
    String rename_contig_prefix="scaffold"
    Float uniquekmer=1000
    String bbtools_container="microbiomedata/bbtools:38.96"
    String spades_container="microbiomedata/spades:3.15.0"
    Boolean input_interleaved = true
    Array[File] input_fq1
    Array[File] input_fq2
    
    if (!input_interleaved) {
        ## the zip() function generates an array of pairs, use .left and .right to access
        scatter(file in zip(input_fq1,input_fq2)){
            call interleave_reads {
                input:
                    input_files = [file.left,file.right],
                    output_file = basename(file.left) + "_" + basename(file.right),
                    container = bbtools_container
           }
        }
    }
    Array[File]? interleaved_input_fastqs = if (input_interleaved) then input_file else interleave_reads.out_fastq

    call bbcms {
          input: input_files=interleaved_input_fastqs, 
                 container=bbtools_container, memory=memory
    }
    call assy {
         input: infile1=bbcms.out1, infile2=bbcms.out2, container=spades_container, threads=threads
    }
    call create_agp {
         input: scaffolds_in=assy.out, container=bbtools_container, rename_contig_prefix = rename_contig_prefix, memory=memory
    }
    call read_mapping_pairs {
         input: reads=interleaved_input_fastqs, ref=create_agp.outcontigs, container=bbtools_container, memory=memory, threads=threads
    }
    if (defined(outdir)) {
        call make_output {
             input: outdir=outdir,
                    contigs=create_agp.outcontigs,
                    scaffolds=create_agp.outscaffolds,
                    agp=create_agp.outagp,
                    bam=read_mapping_pairs.outbamfile,
                    samgz=read_mapping_pairs.outsamfile,
                    covstats=read_mapping_pairs.outcovfile,
                    asmstats=create_agp.outstats,
                    container=bbtools_container
        }
    }
    output {
        File contig = create_agp.outcontigs
        File scaffold = create_agp.outscaffolds
        File agp=create_agp.outagp
        File bam=read_mapping_pairs.outbamfile
        File samgz=read_mapping_pairs.outsamfile
        File covstats=read_mapping_pairs.outcovfile
        File asmstats=create_agp.outstats
        File? final_contig = make_output.outcontigs
        File? final_scaffold = make_output.outscaffolds
        File? final_agp = make_output.outagp
        File? final_covstat = make_output.outcovstats
        File? final_samgz = make_output.outsamgz
        File? final_bam = make_output.outbam
        File? final_asmstat = make_output.outasmstats
    }
    parameter_meta{
	input_file: "illumina paired-end interleaved fastq files"
	outdir: "the final output directory path"
	rename_contig_prefix: "contig prefix for fasta header, default: scaffold"
	final_contig: "assembled contigs fasta file"
	final_scaffold: "assembled scaffold fasta file"
	final_agp: "assembled AGP file"
	final_covstat: "contig coverage stats file"
	final_samgz: "reads aligned to contigs sam file with gz compressed"
	final_bam: "reads aligned to contigs bam file"
	final_asmstat: "assembled scaffold/contigs statistical numbers"
        memory: "optional for jvm memory for bbtools, ex: 32G"
        threads: "optional for jvm/spades threads for bbtools ex: 16"
    }

    meta {
        author: "Chienchi Lo, B10, LANL"
        email: "chienchi@lanl.gov"
        version: "1.0.0"
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

task read_mapping_pairs{
    Array[File] reads
    File ref
    String container
    String? memory
    String? threads

    String filename_resources="resources.log"
    String filename_unsorted="pairedMapped.bam"
    String filename_outsam="pairedMapped.sam.gz"
    String filename_sorted="pairedMapped_sorted.bam"
    String filename_sorted_idx="pairedMapped_sorted.bam.bai"
    String filename_bamscript="to_bam.sh"
    String filename_cov="covstats.txt"
    String filename_cov2="covstats2.txt"
    String filename_errlog="stderr.log"
    String system_cpu="$(grep \"model name\" /proc/cpuinfo | wc -l)"
    String jvm_threads=select_first([threads,system_cpu])
    runtime {
            docker: container
            memory: "120 GiB"
	    cpu:  16
	    maxRetries: 1
     }
    command{
        echo $(curl --fail --max-time 10 --silent http://169.254.169.254/latest/meta-data/public-hostname)
        touch ${filename_resources};
        curl --fail --max-time 10 --silent https://bitbucket.org/berkeleylab/jgi-meta/get/master.tar.gz | tar --wildcards -zxvf - "*/bin/resources.bash" && ./*/bin/resources.bash > ${filename_resources} &
        sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        set -eo pipefail
        if [[ ${reads[0]}  == *.gz ]] ; then
             cat ${sep=" " reads} > infile.fastq.gz
             export mapping_input="infile.fastq.gz"
        fi
        if [[ ${reads[0]}  == *.fastq ]] ; then
             cat ${sep=" " reads} > infile.fastq
             export mapping_input="infile.fastq"
        fi
	
	bbmap.sh -Xmx${default="105G" memory} threads=${jvm_threads} nodisk=true interleaved=true ambiguous=random in=$mapping_input ref=${ref} out=${filename_unsorted} scafstats=${filename_cov2} covstats=${filename_cov} bamscript=${filename_bamscript} 2> >(tee -a ${filename_errlog} >&2) 
        samtools sort -m100M -@ ${jvm_threads} ${filename_unsorted} -o ${filename_sorted}
        samtools index ${filename_sorted}
        reformat.sh -Xmx${default="105G" memory} in=${filename_unsorted} out=${filename_outsam} overwrite=true
	cat ${filename_errlog} | grep 'Percent mapped' | perl -ne 'print "#$_"' > mapping_stats.txt
        cat ${filename_cov} >> mapping_stats.txt
        cp mapping_stats.txt ${filename_cov}
        rm $mapping_input
  }
  output{
      File outbamfile = filename_sorted
      File outbamfileidx = filename_sorted_idx
      File outcovfile = filename_cov
      File outcovfile2 = filename_cov2
      File outsamfile = filename_outsam
      File outresources = filename_resources
  }
}

task create_agp {
    File scaffolds_in
    String? memory
    String container
    String rename_contig_prefix
    String filename_resources="resources.log"
    String prefix="assembly"
    String filename_contigs="${prefix}_contigs.fna"
    String filename_scaffolds="${prefix}_scaffolds.fna"
    String filename_agp="${prefix}.agp"
    String filename_legend="${prefix}_scaffolds.legend"
    runtime {
            docker: container
            memory: "120 GiB"
	    cpu:  16
     }
    command{
	echo $(curl --fail --max-time 10 --silent http://169.254.169.254/latest/meta-data/public-hostname)
        touch ${filename_resources};
        curl --fail --max-time 10 --silent https://bitbucket.org/berkeleylab/jgi-meta/get/master.tar.gz | tar --wildcards -zxvf - "*/bin/resources.bash" && ./*/bin/resources.bash > ${filename_resources} &	
        sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        fungalrelease.sh -Xmx${default="105G" memory} in=${scaffolds_in} out=${filename_scaffolds} outc=${filename_contigs} agp=${filename_agp} legend=${filename_legend} mincontig=200 minscaf=200 sortscaffolds=t sortcontigs=t overwrite=t
        if [ "${rename_contig_prefix}" != "scaffold" ]; then
            sed -i 's/scaffold/${rename_contig_prefix}_scf/g' ${filename_contigs} ${filename_scaffolds} ${filename_agp} ${filename_legend}
        fi
	bbstats.sh format=8 in=${filename_scaffolds} out=stats.json
	sed -i -e 's/l_gt50k/l_gt50K/g' -e 's/.*\/\(.*scaffolds.fna\"\)/\"filename\": \"\1/g' stats.json
    }
    output{
	File outcontigs = filename_contigs
	File outscaffolds = filename_scaffolds
	File outagp = filename_agp
	File outstats = "stats.json"
    	File outlegend = filename_legend
    	File outresources = filename_resources
    }
}

task assy {
     File infile1
     File infile2
     String container
     String? threads
     String filename_resources="resources.log"
     String outprefix="spades3"
     String filename_outfile="${outprefix}/scaffolds.fasta"
     String filename_spadeslog ="${outprefix}/spades.log"
     String system_cpu="$(grep \"model name\" /proc/cpuinfo | wc -l)"
     String spades_cpu=select_first([threads,system_cpu])
     runtime {
            docker: container
            memory: "120 GiB"
	    cpu:  16
     }
     command{
        echo $(curl --fail --max-time 10 --silent http://169.254.169.254/latest/meta-data/public-hostname)
        touch ${filename_resources};
        curl --fail --max-time 10 --silent https://bitbucket.org/berkeleylab/jgi-meta/get/master.tar.gz | tar --wildcards -zxvf - "*/bin/resources.bash" && ./*/bin/resources.bash > ${filename_resources} &		
        sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        set -eo pipefail

        spades.py -m 2000 -o ${outprefix} --only-assembler -k 33,55,77,99,127  --meta -t ${spades_cpu} -1 ${infile1} -2 ${infile2}
     }
     output {
            File out = filename_outfile
            File outlog = filename_spadeslog
            File outresources = filename_resources
     }
}

task bbcms {
     Array[File] input_files
     String container
     String? memory

     String filename_resources="resources.log"
     String filename_outfile="input.corr.fastq.gz"
     String filename_outfile1="input.corr.left.fastq.gz"
     String filename_outfile2="input.corr.right.fastq.gz"
     String filename_readlen="readlen.txt"
     String filename_outlog="stdout.log"
     String filename_errlog="stderr.log"
     String filename_kmerfile="unique31mer.txt"
     String filename_counts="counts.metadata.json"
     runtime {
            docker: container
            memory: "120 GiB"
	    cpu:  16
     }

     command {
        echo $(curl --fail --max-time 10 --silent http://169.254.169.254/latest/meta-data/public-hostname)
        touch ${filename_resources};
        curl --fail --max-time 10 --silent https://bitbucket.org/berkeleylab/jgi-meta/get/master.tar.gz | tar --wildcards -zxvf - "*/bin/resources.bash" && ./*/bin/resources.bash > ${filename_resources} &		
        sleep 30
        export TIME="time result\ncmd:%C\nreal %es\nuser %Us \nsys  %Ss \nmemory:%MKB \ncpu %P"
        set -eo pipefail
        if file --mime -b ${input_files[0]} | grep gzip; then
             cat ${sep=" " input_files} > infile.fastq.gz
             export bbcms_input="infile.fastq.gz"
        fi
	if file --mime -b ${input_files[0]} | grep plain; then
             cat ${sep=" " input_files} > infile.fastq
             export bbcms_input="infile.fastq"
        fi
        bbcms.sh -Xmx${default="105G" memory} metadatafile=${filename_counts} mincount=2 highcountfraction=0.6 in=$bbcms_input out=${filename_outfile} > >(tee -a ${filename_outlog}) 2> >(tee -a ${filename_errlog} >&2) && grep Unique ${filename_errlog} | rev |  cut -f 1 | rev  > ${filename_kmerfile}
        reformat.sh -Xmx${default="105G" memory} in=${filename_outfile} out1=${filename_outfile1} out2=${filename_outfile2}
        readlength.sh -Xmx${default="105G" memory} in=${filename_outfile} out=${filename_readlen}
        rm $bbcms_input
     }
     output {
            File out = filename_outfile
            File out1 = filename_outfile1
            File out2 = filename_outfile2
            File outreadlen = filename_readlen
            File stdout = filename_outlog
            File stderr = filename_errlog
            File outcounts = filename_counts
            File outkmer = filename_kmerfile
            File outresources = filename_resources
     }
}

task interleave_reads{

        Array[File] input_files
        String output_file = "interleaved.fastq.gz"
        String container
        
        command <<<
            if file --mime -b ${input_files[0]} | grep gzip > /dev/null ; then 
                paste <(gunzip -c ${input_files[0]} | paste - - - -) <(gunzip -c ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}
                echo ${output_file}
            else
                if [[ "${output_file}" == *.gz ]]; then
                    paste <(cat ${input_files[0]} | paste - - - -) <(cat ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}
                    echo ${output_file}
                else
                    paste <(cat ${input_files[0]} | paste - - - -) <(cat ${input_files[1]} | paste - - - -) | tr '\t' '\n' | gzip -c > ${output_file}.gz
                    echo ${output_file}.gz
                fi
            fi
        >>>
        
        runtime {
            docker: container
            memory: "1 GiB"
            cpu:  1
        }
        
        output {
                File out_fastq = read_string(stdout())
        }
}
