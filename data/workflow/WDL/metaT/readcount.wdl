# metaT read count workflow
version 1.0

workflow readcount {

  input{
    String proj_id
    File bam
    File gff
    File? map
    String out
    String rna_type
    String container = "dongyingwu/rnaseqct@sha256:e7418cc7a5a58eb138c3b739608d2754a05fa3648b5881befbfbb0bb2e62fa95"
    Int cpu = 1
    String memory = "100G"
    String time = "6:00:00"
  }

  call prepare {
    input: 
    rna_type=rna_type,
    gff = gff,
    map = map,
    container = container,
    cpu = cpu,
    memory = memory,
    time = time
    }

  call count {
    input: 
    bam = bam, 
    gff = gff, 
    out = out,
    map = prepare.map, 
    rna_type=prepare.type_list[0], 
    container = container,
    cpu = cpu,
    memory = memory,
    time = time
    } 

  call make_info_file{
    input:
    container = container,
    cpu = cpu,
    memory = memory,
    time = time,
    proj_id = proj_id
  }

  output{
   File count_table = count.tab
   File? count_ig = count.ig
   File? count_log = count.log
   File info_file = make_info_file.readcount_info
   
  }
  parameter_meta {
	  proj_id: "NMDC project ID"
    bam: "BAM file output from MetaT Assembly"
    gff: "Functional GFF file output from MetaG Annotation"
    out: "Out directory or string to name files"
    rna_type: "RNA strandedness, either 'aRNA' or 'non_stranded_RNA'"
	}
}

task prepare  {
  input{
    String rna_type 
    File gff
    File? map
    String mapped = if (defined(map)) then true else false
    String mapfile = "mapfile.map" 
    String container
    Int cpu
    String memory
    String time
  }

  command <<<
    set -eou pipefail
    # generate map file from gff scaffold names

    if [ "~{mapped}"  = true ] ; then
      ln -s ~{map} ~{mapfile} || ln ~{map} ~{mapfile}  
      else  
          awk '{print $1 "\t" $1}' ~{gff} > ~{mapfile}
     fi

    if [ ~{rna_type} == 'aRNA' ]
      then 
        echo ' -aRNA yes '
    elif [ ~{rna_type} == 'non_stranded_RNA' ] 
      then
        echo ' -non_stranded yes '
    else
        echo '  '
    fi
  >>>

  output{
    File map = "mapfile.map" 
    Array[String] type_list=read_lines(stdout())
   }

   runtime {
        docker: container
        cpu: cpu
        memory: memory
        time: time
    }
 }


task count {
  input{
    File bam
    File map
    File gff
    String out
    String rna_type
    String container
    Int cpu
    String memory
    String time
  }

  command <<< 
  set -eou pipefail
    ls -lah /usr/bin/readCov_metaTranscriptome_2k20.pl
    readCov_metaTranscriptome_2k20.pl  \
    -b ~{bam} \
    -m ~{map} \
    -g ~{gff} \
    -o ~{out} \
    ~{rna_type}
    >>>

  output{
   File tab=out
   File? log="~{out}"+".Stats.log"
   File? ig="~{out}"+".intergenic"
  }
 
    runtime {
        docker: container
        cpu: cpu
        memory: memory
        time: time
    }

}

task make_info_file {
  input{
    String container
    Int cpu
    String memory
    String time
    String proj_id
    String prefix = sub(proj_id, ":", "_")
  }

  command <<< 
  set -euo pipefail
  echo -e "MetaT Workflow - Read Counts Info File" > ~{prefix}_readcount.info
  echo -e "This workflow outputs a tab separated read count file from BAM and GFF using SAMTOOLS(1):" >> ~{prefix}_readcount.info
  echo -e "`samtools --version | head -2`"  >> ~{prefix}_readcount.info

  echo -e "\nContainer: ~{container}"  >> ~{prefix}_readcount.info
  
  echo -e "\n(1) Danecek, P., Bonfield, J. K., Liddle, J., Marshall, J., Ohan, V., Pollard, M. O., Whitwham, A., Keane, T., McCarthy, S. A., Davies, R. M., & Li, H. (2021). Twelve years of samtools and bcftools. GigaScience, 10(2), giab008. https://doi.org/10.1093/gigascience/giab008" >>  ~{prefix}_readcount.info # samtools

    >>>

  output{
   File readcount_info = "~{prefix}_readcount.info"
  }
 
    runtime {
        docker: container
        cpu: cpu
        memory: memory
        time: time
    }

}
