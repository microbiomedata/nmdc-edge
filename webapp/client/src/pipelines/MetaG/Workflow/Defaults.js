import { colors } from '../../../common/Colors';
export const defaults = {
    //onSubmit, onBlur, onChange
    form_mode: 'onChange',

    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
    { value: 'ReadsQC', label: 'ReadsQC' },
    { value: 'ReadbasedAnalysis', label: 'Read-based Taxonomy Classification' },
    { value: 'MetaAssembly', label: 'Metagenome Assembly' },
    { value: 'MetaAnnotation', label: 'Metagenome Annotation' },
    { value: 'MetaMAGs', label: 'Metagenome MAGs' },
];

export const workflowInputTips = {
    ReadsQC: {
        fastq_tip: 'ReadsQC requires paired-end Illumina data in FASTQ format as the input; the file can be interleaved and can becompressed. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    ReadbasedAnalysis: {
        fastq_tip: 'Input is single- or paired-end sequencing files (This can be the output from ReadsQC Workflow.) <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaAssembly: {
        fastq_tip: 'Metagenome Assembly requires paired-end Illumina data as an FASTQ file. This input can be the output from the ReadsQC workflow. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaAnnotation: {
        fasta_tip: 'Metagenome Annotation requires a .fasta file of assembled contigs. This input can be the output of the Metagenome Assembly workflow. <br/>Acceptable file formats: .fasta, .fa, .fna<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaMAGs: {
        contig_tip: 'Input contig<br />Note: The file size limit for the URL input is 10GB',
        sam_tip: 'Input sam or bam file<br />Note: The file size limit for the URL input is 10GB',
        gff_tip: 'input gff<br />Note: The file size limit for the URL input is 10GB',
        map_tip: 'input map<br />Note: The file size limit for the URL input is 10GB'
    },
}

export const workflowlist = {
    ReadsQC: {
        title: 'ReadsQC',
        name: 'ReadsQC Workflow',
        img: '/docs/images/ReadsQC.png',
        thumbnail: '/docs/images/ReadsQC-thumbnail.png',
        video:'/docs/videos/ReadsQC.mp4',
        pdf:'/docs/help/ReadsQC.pdf',
        link: 'https://github.com/microbiomedata/ReadsQC',
        doclink: 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/1_RQC_index.html',
        info: 'This workflow is a replicate of the QA protocol implemented at JGI for Illumina reads and use the program “rqcfilter2” from BBTools(38:44) which implements them as a pipeline.'
    },
    ReadbasedAnalysis: {
        title: 'Read-based Taxonomy Classification',
        name: 'Read-based Taxonomy Classification Workflow',
        img: '/docs/images/ReadBasedAnalysis.png',
        thumbnail: '/docs/images/ReadBasedAnalysis-thumbnail.png',
        video:'/docs/videos/ReadBasedAnalysis.mp4',
        pdf:'/docs/help/ReadBasedAnalysis.pdf',
        link: 'https://github.com/microbiomedata/ReadbasedAnalysis',
        doclink: 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/2_ReadAnalysis_index.html',
        info: 'The pipeline takes sequencing files (single- or paired-end) and profiles them using multiple taxonomic classification tools.'
    },
    MetaAssembly: {
        title: 'Metagenome Assembly',
        name: 'Metagenome Assembly Workflow',
        img: '/docs/images/MetagenomeAssembly.png',
        thumbnail: '/docs/images/MetagenomeAssembly-thumbnail.png',
        video:'/docs/videos/MetagenomeAssembly.mp4',
        pdf:'/docs/help/MetagenomeAssembly.pdf',
        link: 'https://github.com/microbiomedata/metaAssembly',
        doclink: 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/3_MetaGAssemly_index.html',
        info: 'It take paired-end reads runs error correction by bbcms (BBTools). The clean reads are assembled by MetaSpades. After assembly, the reads are mapped back to contigs by bbmap (BBTools) for coverage information.'
    },
    MetaAnnotation: {
        title: 'Metagenome Annotation',
        name: 'Metagenome Annotation Workflow',
        img: '/docs/images/MetagenomeAnnotation.png',
        thumbnail: '/docs/images/MetagenomeAnnotation-thumbnail.png',
        //video:'/docs/videos/MetagenomeAnnotation.mp4',
        pdf:'/docs/help/MetagenomeAnnotation.pdf',
        link: 'https://github.com/microbiomedata/mg_annotation',
        doclink: 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/4_MetaGAnnotation_index.html',
        info: 'It takes assembled metagenomes and generates structrual and functional annotations.'
    },
    MetaMAGs: {
        title: 'Metagenome MAGs',
        name: 'Metagenome MAGs Workflow',
        img: '/docs/images/MetagenomeMAGs.png',
        thumbnail: '/docs/images/MetagenomeMAGs-thumbnail.png',
        link: 'https://github.com/microbiomedata/metaMAGs',
        info: 'The workflow is based on IMG MAGs pipeline for metagenome assembled genomes generation.'
    },
}

export const initialReadbasedAnalysis = {
    validForm: false,
    errMessage: '',
    enabled_tools: {
        "gottcha2": false,
        "kraken2": false,
        "centrifuge": false
    },
    fastqPaired: [],
    fastqSingle: [],
    'paired-input-max': 1,
    paired: true,
    tool_options: [
        { value: 'gottcha2', label: 'GOTTCHA2' },
        { value: 'kraken2', label: 'Kraken2' },
        { value: 'centrifuge', label: 'Centrifuge' },
    ],
    fastqPairedDisplay: [],
    fastqSingleDisplay: [],
}

export const initialMetaAnnotation = {
    validForm: false,
    errMessage: '',
    input_fasta: '',
    input_fasta_validInput: false,
    input_fasta_display: ''
}

export const initialMetaAssembly = {
    validForm: false,
    errMessage: '',
    input_fastq: [],
}

export const initialMetaMAGs = {
    validForm: false,
    errMessage: '',
    input_contig: '',
    input_sam: '',
    input_gff: '',
    input_map: '',
    input_contig_validInput: false,
    input_sam_validInput: false,
    input_gff_validInput: false,
    input_map_validInput: true,
    input_contig_display: '',
    input_sam_display: '',
    input_gff_display: '',
    input_map_display: '',
}

export const initialReadsQC = {
    validForm: false,
    errMessage: '',
    input_fastq: [],
    validInputArray: false,
}