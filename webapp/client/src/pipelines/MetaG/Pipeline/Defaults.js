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
        fastq_tip: 'Input is paired-end Illumina data in FASTQ format as the input; the file can be interleaved and can becompressed. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz'
    },
    MetaMAGs: {
        map_tip: 'input map',
        domain_tip: 'input domain'
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
    enabled_tools: {
        "gottcha2": true,
        "kraken2": true,
        "centrifuge": true
    },
    tool_options: [
        { value: 'gottcha2', label: 'GOTTCHA2' },
        { value: 'kraken2', label: 'Kraken2' },
        { value: 'centrifuge', label: 'Centrifuge' },
    ],
    paramsOn: true,
}

export const initialMetaAnnotation = {
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
    input_map_display: '',
    input_domain_display: '',
}