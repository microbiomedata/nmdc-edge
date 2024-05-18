export const workflowlist = {
    ReadsQC: {
        title: 'ReadsQC',
        name: 'ReadsQC Workflow'
    },
    ReadbasedAnalysis: {
        title: 'Read-based Taxonomy Classification',
        name: 'Read-based Taxonomy Classification Workflow'
    },
    MetaAssembly: {
        title: 'Metagenome Assembly',
        name: 'Metagenome Assembly Workflow'
    },
    virus_plasmid: {
        title: 'Viruses and Plasmids',
        name: 'Viruses and Plasmids Workflow'
    },
    MetaAnnotation: {
        title: 'Metagenome Annotation',
        name: 'Metagenome Annotation Workflow'
    },
    MetaMAGs: {
        title: 'Metagenome MAGs',
        name: 'Metagenome MAGs Workflow'
    }
}

export const workflowInputTips = {
    Input: {
        fastq_tip: 'Input is paired-end Illumina data in FASTQ format as the input; the file can be interleaved and can be compressed. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaMAGs: {
        map_tip: 'input map<br />Note: The file size limit for the URL input is 10GB',
        domain_tip: 'input domain<br />Note: The file size limit for the URL input is 10GB'
    },
}

export const initialReadsQC = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
}

export const initialReadbasedAnalysis = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
    enabled_tools: {
        "gottcha2": true,
        "kraken2": true,
        "centrifuge": true
    },
}

export const initialMetaAnnotation = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
}

export const initialVirusPlasmid = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
}

export const initialMetaAssembly = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
}

export const initialMetaMAGs = {
    validForm: true,
    errMessage: '',
    paramsOn: true,
    input_map: '',
    input_domain: '',
    input_map_validInput: true,
    input_domain_validInput: true,
    input_map_display: '',
    input_domain_display: '',
}