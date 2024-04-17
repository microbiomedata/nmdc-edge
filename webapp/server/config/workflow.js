workflowlist = {
  ReadbasedAnalysis: {
    main_wdl: 'metaG/ReadbasedAnalysis.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'ReadbasedAnalysis',
    full_name: 'Read-based Taxonomy Classification',
    inputs_tmpl: 'readbasedAnalysis_inputs.tmpl',
    outdir: 'output/ReadbasedAnalysis',
    cromwell_calls: ['ReadbasedAnalysis'],
    wdl_version: 'draft-2'
  },
  ReadsQC: {
    main_wdl: 'metaG/rqcfilter.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'jgi_rqcfilter',
    full_name: 'ReadsQC',
    inputs_tmpl: 'readsQC_inputs.tmpl',
    options_tmpl: 'readsQC_options.tmpl',
    outdir: 'output/ReadsQC',
    cromwell_calls: ['jgi_rqcfilter'],
    wdl_version: 'draft-2'
  },
  MetaAnnotation: {
    main_wdl: 'metaG/MetaAnnotation.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'annotation',
    full_name: 'Metagenome Annotation',
    inputs_tmpl: 'metaAnnotation_inputs.tmpl',
    options_tmpl: 'metaAnnotation_options.tmpl',
    outdir: 'output/MetagenomeAnnotation',
    cromwell_calls: ['main_workflow.annotation', 'main_workflow.annotation_out'],
    wdl_version: 'draft-2'
  },
  MetaAssembly: {
    main_wdl: 'metaG/jgi_assembly.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'jgi_metaASM',
    full_name: 'Metagenome Assembly',
    inputs_tmpl: 'metaAssembly_inputs.tmpl',
    options_tmpl: 'metaAssembly_options.tmpl',
    outdir: 'output/MetagenomeAssembly',
    cromwell_calls: ['jgi_metaASM'],
    wdl_version: 'draft-2'
  },
  MetaMAGs: {
    main_wdl: 'metaG/mbin_nmdc.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'nmdc_mags',
    full_name: 'Metagenome MAGs',
    inputs_tmpl: 'metaMAGs_inputs.tmpl',
    options_tmpl: 'metaMAGs_options.tmpl',
    outdir: 'output/MetagenomeMAGs',
    cromwell_calls: ['nmdc_mags'],
    wdl_version: 'draft-2'
  },
  Metatranscriptome: {
    main_wdl: 'metaT/metaT.wdl',
    wdl_imports: 'metaT/imports.zip',
    name: 'nmdc_metat',
    full_name: 'Metatranscriptome',
    inputs_tmpl: 'metaT_inputs.tmpl',
    options_tmpl: 'metaT_options.tmpl',
    outdir: 'output/Metatranscriptome',
    cromwell_calls: ['nmdc_metat'],
    wdl_version: 'draft-2'
  },
  EnviroMS: {
    main_wdl: 'organicMatter/enviroMS.wdl',
    wdl_imports: 'organicMatter/imports.zip',
    name: 'enviroMS',
    full_name: 'EnviroMS',
    inputs_tmpl: 'enviroMS_inputs.tmpl',
    options_tmpl: 'enviroMS_options.tmpl',
    outdir: 'output/EnviroMS',
    cromwell_calls: ['fticrmsNOM'],
    wdl_version: 'draft-2'
  },
  'virus_plasmid': {
    main_wdl: 'virusPlasmids/viral-plasmid_wf.wdl',
    wdl_imports: 'virusPlasmids/imports.zip',
    name: 'viral',
    full_name: 'virus_plasmid',
    inputs_tmpl: 'virus_plasmid_inputs.tmpl',
    options_tmpl: 'virus_plasmid_options.tmpl',
    outdir: 'output/virus_plasmid',
    cromwell_calls: ['viral'],
    wdl_version: 'draft-2'
  },
  'Metaproteomics': {
    main_wdl: 'metaP/metapro_main.wdl',
    wdl_imports: 'metaP/imports.zip',
    name: 'metapro',
    full_name: 'Metaproteomics',
    inputs_tmpl: 'metaProteomics_inputs.tmpl',
    options_tmpl: 'metaProteomics_options.tmpl',
    outdir: 'output/Metaproteomics',
    cromwell_calls: ['metapro.job_analysis', 'metapro.report_gen', 'metapro.make_output', 'metapro.gen_metadata'],
    wdl_version: '1.0'
  },
  'sra2fastq': {
    main_wdl: 'sra/sra2fastq.wdl',
    wdl_imports: 'sra/imports.zip',
    name: 'sra',
    full_name: 'sra2fastq',
    inputs_tmpl: 'sra2fastq_inputs.tmpl',
    options_tmpl: 'sra2fastq_options.tmpl',
    outdir: 'output/sra2fastq',
    cromwell_calls: ['sra'],
    wdl_version: '1.0'
  },
}

pipelinelist = {
  'Metagenome Pipeline': {
    main_wdl: 'metaG/metagenome_pipeline.wdl',
    wdl_imports: 'metaG/imports.zip',
    name: 'metagenome',
    inputs_tmpl: 'metagenome_pipeline_inputs.tmpl',
    options_tmpl: 'metagenome_pipeline_options.tmpl',
    wdl_version: 'draft-2',
    outdir: 'output',
    workflows: {
      ReadsQC: {
        full_name: 'ReadsQC',
        cromwell_calls: ['main_workflow.jgi_rqcfilter_call']
      },
      ReadbasedAnalysis: {
        full_name: 'Read-based Taxonomy Classification',
        cromwell_calls: ['main_workflow.ReadbasedAnalysis_call']
      },
      MetaAssembly: {
        full_name: 'Metagenome Assembly',
        cromwell_calls: ['main_workflow.metaAssembly_call']
      },
      virus_plasmid: {
        full_name: 'Viral Plasmid',
        cromwell_calls: ['main_workflow.viralPlasmid_call']
      },
      MetaAnnotation: {
        full_name: 'Metagenome Annotation',
        cromwell_calls: ['main_workflow.metaAnnotation_call']
      },
      MetaMAGs: {
        full_name: 'Metagenome MAGs',
        cromwell_calls: ['main_workflow.metaMAGs_call', 'main_workflow.metaMAGs_call.metabat_bins', 'main_workflow.metaMAGs_call.final_hqmq_bins']
      }
    }
  }
}

module.exports = { workflowlist, pipelinelist };