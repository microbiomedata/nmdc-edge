workflowlist = {
    ReadbasedAnalysis: {
        wdl: 'ReadbasedAnalysis.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'ReadbasedAnalysis',
        full_name: 'Read-based Taxonomy Classification',
        wdl_tmpl: 'readbasedAnalysis_wdl.tmpl',
        inputs_tmpl: 'readbasedAnalysis_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/ReadbasedAnalysis',
        cromwell_calls: ['main_workflow.ReadbasedAnalysis'],
        wdl_version: 'draft-2'
    },
    ReadsQC: {
        wdl: 'rqcfilter.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'jgi_rqcfilter',
        full_name: 'ReadsQC',
        wdl_tmpl: 'readsQC_wdl.tmpl',
        inputs_tmpl: 'readsQC_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/ReadsQC',
        cromwell_calls: ['main_workflow.jgi_rqcfilter'],
        wdl_version: '1.0'
    },
    MetaAnnotation: {
        wdl: 'annotation_full.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'annotation',
        full_name: 'Metagenome Annotation',
        wdl_tmpl: 'metaAnnotation_wdl.tmpl',
        inputs_tmpl: 'metaAnnotation_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeAnnotation',
        cromwell_calls: ['main_workflow.annotation'],
        wdl_version: 'draft-2'
    },
    MetaAssembly: {
        wdl: 'nmdcEDGE_assembly.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'jgi_metaASM',
        full_name: 'Metagenome Assembly',
        wdl_tmpl: 'metaAssembly_wdl.tmpl',
        inputs_tmpl: 'metaAssembly_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeAssembly',
        cromwell_calls: ['main_workflow.jgi_metaASM'],
        wdl_version: 'draft-2'
    },
    MetaMAGs: {
        wdl: 'mbin_nmdc.wdl',
        wdl_imports: 'metaG/imports.zip',
        name: 'nmdc_mags',
        full_name: 'Metagenome MAGs',
        wdl_tmpl: 'metaMAGs_wdl.tmpl',
        inputs_tmpl: 'metaMAGs_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/MetagenomeMAGs',
        cromwell_calls: ['main_workflow.nmdc_mags'],
        wdl_version: 'draft-2'
    },
    Metatranscriptome: {
        wdl: 'metaT.wdl',
        wdl_imports: 'metaT/imports.zip',
        name: 'nmdc_metat',
        full_name: 'Metatranscriptomics',
        wdl_tmpl: 'metaT_wdl.tmpl',
        inputs_tmpl: 'metaT_inputs.tmpl',
        options_json: 'metaT_options.json',
        outdir: 'output/Metatranscriptomics',
        cromwell_calls: ['main_workflow.nmdc_metat'],
        wdl_version: 'draft-2'
    },
    EnviroMS: {
        wdl: 'enviroMS.wdl',
        wdl_imports: 'organicMatter/imports.zip',
        name: 'enviroMS',
        full_name: 'Natural Organic Matter',
        wdl_tmpl: 'enviroMS_wdl.tmpl',
        inputs_tmpl: 'enviroMS_inputs.tmpl',
        options_json: 'enviroMS_options.json',
        outdir: 'output/NOM',
        cromwell_calls: ['main_workflow.enviroMS'],
        wdl_version: 'draft-2'
    },
    'virus_plasmid': {
        wdl: 'viral-plasmid_wf.wdl',
        wdl_imports: 'virusPlasmids/imports.zip',
        name: 'viral',
        full_name: 'Viruses and Plasmids',
        wdl_tmpl: 'virus_plasmid_wdl.tmpl',
        inputs_tmpl: 'virus_plasmid_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/virus_plasmid',
        cromwell_calls: ['main_workflow.viral'],
        wdl_version: 'draft-2'
    },
    'Metaproteomics': {
        wdl_pipeline: 'metaP/metapro_main.wdl',
        wdl_imports: 'metaP/imports.zip',
        name: 'metapro',
        full_name: 'Metaproteomics',
        wdl_tmpl: 'metaProteomics_wdl.tmpl',
        inputs_tmpl: 'metaProteomics_inputs.tmpl',
        options_json: 'metaG_options.tmpl',
        outdir: 'output/Metaproteomics',
        cromwell_calls: ['metapro.job_analysis','metapro.report_gen','metapro.make_output','metapro.gen_metadata'],
        wdl_version: '1.0'
    },
    'sra2fastq': {
        wdl: 'sra2fastq.wdl',
        wdl_imports: 'sra/imports.zip',
        name: 'sra',
        full_name: 'Retrieve SRA Data',
        wdl_tmpl: 'sra2fastq_wdl.tmpl',
        inputs_tmpl: 'sra2fastq_inputs.tmpl',
        options_json: 'sra2fast_options.json',
        outdir: 'output/sra2fastq',
        cromwell_calls: ['main_workflow.sra'],
        wdl_version: '1.0'
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
        wdl_version: '1.0',
        outdir: 'output',
        workflows: {
            ReadsQC: {
                full_name: 'ReadsQC',
                cromwell_calls: ['main_workflow.jgi_rqcfilter_call', 'main_workflow.nmdc_rqcfilter_call']
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
