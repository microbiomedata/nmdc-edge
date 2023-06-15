workflowlist = {
    ReadbasedAnalysis: {
        wdl: 'ReadbasedAnalysis.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'ReadbasedAnalysis',
        full_name: 'Read-based Taxonomy Classification',
        wdl_tmpl: 'readbasedAnalysis_wdl.tmpl',
        inputs_tmpl: 'readbasedAnalysis_inputs.tmpl',
        outdir: 'output/ReadbasedAnalysis',
        cromwell_calls: ['main_workflow.ReadbasedAnalysis']
    },
    ReadsQC: {
        wdl: 'rqcfilter.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'jgi_rqcfilter',
        full_name: 'ReadsQC',
        wdl_tmpl: 'readsQC_wdl.tmpl',
        inputs_tmpl: 'readsQC_inputs.tmpl',
        options_json: 'readsQC_options.json',
        outdir: 'output/ReadsQC',
        cromwell_calls: ['main_workflow.jgi_rqcfilter']
    },
    MetaAnnotation: {
        wdl: 'annotation.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'annotation',
        full_name: 'Metagenome Annotation',
        wdl_tmpl: 'metaAnnotation_wdl.tmpl',
        inputs_tmpl: 'metaAnnotation_inputs.tmpl',
        options_json: 'metaAnnotation_options.json',
        outdir: 'output/MetagenomeAnnotation',
        cromwell_calls: ['main_workflow.annotation']
    },
    MetaAssembly: {
        wdl: 'jgi_assembly.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'jgi_metaASM',
        full_name: 'Metagenome Assembly',
        wdl_tmpl: 'metaAssembly_wdl.tmpl',
        inputs_tmpl: 'metaAssembly_inputs.tmpl',
        options_json: 'metaAssembly_options.json',
        outdir: 'output/MetagenomeAssembly',
        cromwell_calls: ['main_workflow.jgi_metaASM']
    },
    MetaMAGs: {
        wdl: 'mbin_nmdc.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'nmdc_mags',
        full_name: 'Metagenome MAGs',
        wdl_tmpl: 'metaMAGs_wdl.tmpl',
        inputs_tmpl: 'metaMAGs_inputs.tmpl',
        options_json: 'metaMAGs_options.json',
        outdir: 'output/MetagenomeMAGs',
        cromwell_calls: ['main_workflow.nmdc_mags']
    },
    Metatranscriptome: {
        wdl: 'metaT.wdl',
        wdl_imports: 'metaT/imports.zip',
        name: 'nmdc_metat',
        full_name: 'Metatranscriptome',
        wdl_tmpl: 'metaT_wdl.tmpl',
        inputs_tmpl: 'metaT_inputs.tmpl',
        options_json: 'metaT_options.json',
        outdir: 'output/Metatranscriptome',
        cromwell_calls: ['main_workflow.nmdc_metat']
    },
    EnviroMS: {
        wdl: 'enviroMS.wdl',
        wdl_imports: 'organicMatter/imports.zip',
        name: 'enviroMS',
        full_name: 'EnviroMS',
        wdl_tmpl: 'enviroMS_wdl.tmpl',
        inputs_tmpl: 'enviroMS_inputs.tmpl',
        options_json: 'enviroMS_options.json',
        outdir: 'output/EnviroMS',
        cromwell_calls: ['main_workflow.enviroMS']
    },
    'virus_plasmid': {
        wdl: 'viral-plasmid_wf.wdl',
        wdl_imports: 'virusPlasmids/imports.zip',
        name: 'viral',
        full_name: 'virus_plasmid',
        wdl_tmpl: 'virus_plasmid_wdl.tmpl',
        inputs_tmpl: 'virus_plasmid_inputs.tmpl',
        options_json: 'virus_plasmid_options.json',
        outdir: 'output/virus_plasmid',
        cromwell_calls: ['main_workflow.viral']
    },
    'Metaproteomics': {
        wdl: 'metapro_main.wdl',
        wdl_imports: 'metaP/imports.zip',
        name: 'metapro',
        full_name: 'Metaproteomics',
        wdl_tmpl: 'metaProteomics_wdl.tmpl',
        inputs_tmpl: 'metaProteomics_inputs.tmpl',
        options_json: 'metaProteomics_options.json',
        outdir: 'output/Metaproteomics',
        cromwell_calls: ['main_workflow.metapro']
    },
    'sra2fastq': {
        wdl: 'sra2fastq.wdl',
        wdl_imports: 'sra/imports.zip',
        name: 'sra',
        full_name: 'sra2fastq',
        wdl_tmpl: 'sra2fastq_wdl.tmpl',
        inputs_tmpl: 'sra2fastq_inputs.tmpl',
        options_json: 'sra2fast_options.json',
        outdir: 'output/sra2fastq',
        cromwell_calls: ['main_workflow.sra']
    },
}

pipelinelist = {
    'Metagenome Pipeline': {
        wdl: 'metagenome_pipeline.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'metagenome',
        wdl_tmpl: 'metagenome_pipeline_wdl.tmpl',
        inputs_tmpl: 'metagenome_pipeline_inputs.tmpl',
        options_json: 'metagenome_pipeline_options.json',
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