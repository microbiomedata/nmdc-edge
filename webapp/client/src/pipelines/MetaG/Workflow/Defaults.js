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
        fastq_tip: 'Input is single- or paired-end sequencing files (This can be the output from ReadsQC Workflow. Interleaved files are treated as single end.) <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaAssembly: {
        fastq_tip: 'Metagenome Assembly requires paired-end Illumina data as an FASTQ file. This input can be the output from the ReadsQC workflow. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaAnnotation: {
        fasta_tip: 'Metagenome Annotation requires a .fasta file of assembled contigs. This input can be the output of the Metagenome Assembly workflow. <br/>Acceptable file formats: .fasta, .fa, .fna<br />Note: The file size limit for the URL input is 10GB'
    },
    MetaMAGs: {
        contig_file: 'The assembly_contigs.fna of the Metagenome Assembly workflow output<br />Note: The file size limit for the URL input is 10GB',
        sam_file: 'The &lt;prefix&gt;_sorted.bam of the Metagenome Assembly workflow output<br />Note: The file size limit for the URL input is 10GB',
        proteins_file: 'The &lt;prefix&gt;_proteins.faa of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        gff_file: 'The &lt;prefix&gt;_functional_annotation.gff of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        cog_file: 'The &lt;prefix&gt;_cog.gff of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        ec_file: 'The &lt;prefix&gt;_ec.tsv of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        ko_file: 'The &lt;prefix&gt;_ko.tsv of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        pfam_file: 'The &lt;prefix&gt;_pfam.gff of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        tigrfam_file: 'The &lt;prefix&gt;_tigrfam.gff of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        crispr_file: 'The &lt;prefix&gt;_crt.crisprs of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        product_names_file: 'The &lt;prefix&gt;_product_names.tsv of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        gene_phylogeny_file: 'The &lt;prefix&gt;_gene_phylogeny.tsv of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        lineage_file: 'The &lt;prefix&gt;_scaffold_lineage.tsv of the Metagenome Annotation workflow output<br />Note: The file size limit for the URL input is 10GB',
        map_file: 'MAP file containing mapping of contig headers to annotation IDs<br />Note: The file size limit for the URL input is 10GB',
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
    sam_file: '',
    contig_file: '',
    proteins_file: '',
    gff_file: '',
    cog_file: '',
    ec_file: '',
    ko_file: '',
    pfam_file: '',
    tigrfam_file: '',
    crispr_file: '',
    product_names_file: '',
    gene_phylogeny_file: '',
    lineage_file: '',
    map_file: '',
    sam_file_validInput: false,
    contig_file_validInput: false,
    proteins_file_validInput: false,
    gff_file_validInput: false,
    cog_file_validInput: false,
    ec_file_validInput: false,
    ko_file_validInput: false,
    pfam_file_validInput: false,
    tigrfam_file_validInput: false,
    crispr_file_validInput: false,
    product_names_file_validInput: false,
    gene_phylogeny_file_validInput: false,
    lineage_file_validInput: false,
    map_file_validInput: true,
    sam_file_display: '',
    contig_file_display: '',
    proteins_file_display: '',
    gff_file_display: '',
    cog_file_display: '',
    ec_file_display: '',
    ko_file_display: '',
    pfam_file_display: '',
    tigrfam_file_display: '',
    crispr_file_display: '',
    product_names_file_display: '',
    gene_phylogeny_file_display: '',
    lineage_file_display: '',
    map_file_display: '',
    contig_file_autoFill: false,
    gff_file_autoFill: false,
    cog_file_autoFill: false,
    ec_file_autoFill: false,
    ko_file_autoFill: false,
    pfam_file_autoFill: false,
    tigrfam_file_autoFill: false,
    crispr_file_autoFill: false,
    product_names_file_autoFill: false,
    gene_phylogeny_file_autoFill: false,
    lineage_file_autoFill: false,
    metaAssemblyOutputFiles: {
        //contig_file: 'assembly_contigs.fna',
        //sam_file: '_sorted.bam',
    },
    metaAnnotationOutputFiles: {
        //proteins_file:'_proteins.faa',
        contig_file: '_contigs.fna',
        gff_file: '_functional_annotation.gff',
        cog_file: '_cog.gff',
        ec_file: '_ec.tsv',
        ko_file: '_ko.tsv',
        pfam_file: '_pfam.gff',
        tigrfam_file: '_tigrfam.gff',
        cath_funfam_file: '_cath_funfam.gff',
        smart_file: '_smart.gff',
        supfam_file: '_supfam.gff',
        crispr_file: '_crt.crisprs',
        product_names_file: '_product_names.tsv',
        gene_phylogeny_file: '_gene_phylogeny.tsv',
        lineage_file: '_scaffold_lineage.tsv',
        map_file: '_contig_names_mapping.tsv',
    }
}

export const initialReadsQC = {
    validForm: false,
    errMessage: '',
    input_fastq: [],
    validInputArray: false,
}