workflowlist = {
    ReadbasedAnalysis: {
        wdl_imports: 'metaG/imports.zip',
        full_name: 'Read-based Taxonomy Classification',
        wdl_wrapper: 'readbasedAnalysis_wrapper.wdl',
        inputs_tmpl: 'readbasedAnalysis_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/ReadbasedAnalysis',
        wdl_version: 'draft-2'
    },
    ReadsQC: {
        wdl_imports: 'metaG/imports.zip',
        full_name: 'ReadsQC',
        wdl_wrapper: 'readsQC_wrapper.wdl',
        inputs_tmpl: 'readsQC_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/ReadsQC',
        wdl_version: 'draft-2'
    },
    MetaAnnotation: {
        wdl_imports: 'metaG/imports.zip',
        full_name: 'Metagenome Annotation',
        wdl_wrapper: 'metaAnnotation_wrapper.wdl',
        inputs_tmpl: 'metaAnnotation_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeAnnotation',
        wdl_version: 'draft-2'
    },
    MetaAssembly: {
        wdl_imports: 'metaG/imports.zip',
        full_name: 'Metagenome Assembly',
        wdl_wrapper: 'metaAssembly_wrapper.wdl',
        inputs_tmpl: 'metaAssembly_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeAssembly',
        wdl_version: 'draft-2'
    },
    MetaMAGs: {
        wdl_imports: 'metaG/imports.zip',
        full_name: 'Metagenome MAGs',
        wdl_wrapper: 'metaMAGs_wrapper.wdl',
        inputs_tmpl: 'metaMAGs_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeMAGs',
        wdl_version: 'draft-2'
    },
    Metatranscriptome: {
        wdl_imports: 'metaT/imports.zip',
        full_name: 'Metatranscriptome',
        wdl_wrapper: 'metaT_wrapper.wdl',
        inputs_tmpl: 'metaT_inputs.tmpl',
        options_tmpl: 'metaT_options.json',
        outdir: 'output/Metatranscriptome',
        wdl_version: 'draft-2'
    },
    EnviroMS: {
        wdl_imports: 'organicMatter/imports.zip',
        full_name: 'Natural Organic Matter',
        wdl_wrapper: 'enviroMS_wrapper.wdl',
        inputs_tmpl: 'enviroMS_inputs.tmpl',
        options_tmpl: 'enviroMS_options.json',
        outdir: 'output/EnviroMS',
        wdl_version: 'draft-2'
    },
    'virus_plasmid': {
        wdl_imports: 'virusPlasmids/imports.zip',
        full_name: 'Viruses and Plasmids',
        wdl_wrapper: 'virus_plasmid_wrapper.wdl',
        inputs_tmpl: 'virus_plasmid_inputs.tmpl',
        options_tmpl: 'metaG_options.tmpl',
        outdir: 'output/virus_plasmid',
        wdl_version: 'draft-2'
    },
    'Metaproteomics': {
        wdl_imports: 'metaP/imports.zip',
        full_name: 'Metaproteomics',
        wdl_wrapper: 'metaProteomics_wrapper.wdl',
        inputs_tmpl: 'metaProteomics_inputs.tmpl',
        options_tmpl: 'metaProteomics_options.json',
        outdir: 'output/Metaproteomics',
        wdl_version: '1.0'
    },
    'sra2fastq': {
        wdl_imports: 'sra/imports.zip',
        full_name: 'Retrieve SRA Data',
        wdl_wrapper: 'sra2fastq_wrapper.wdl',
        inputs_tmpl: 'sra2fastq_inputs.tmpl',
        options_tmpl: 'sra2fast_options.json',
        outdir: 'output/sra2fastq',
        wdl_version: '1.0'
    },
}

pipelinelist = {
    'Metagenome Pipeline': {
        wdl_imports: 'metaG/imports.zip',
        wdl_wrapper: 'metagenome_pipeline_wrapper.wdl',
        inputs_tmpl: 'metagenome_pipeline_inputs.tmpl',
        options_tmpl: 'metagenome_pipeline_options.json',
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
                full_name: 'Viruses and Plasmids',
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