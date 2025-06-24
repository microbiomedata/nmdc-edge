export const intro = {
    title: 'Introduction',
    name: 'NMDC EDGE Introduction/Quick Start',
    bgcolor: '#4F3C80'
}

export const pipelinelist = {
    MetaG: {
        title: 'Metagenomics',
        name: 'Metagenomics',
        doclink: {
            'ReadsQC': 'https://docs.microbiomedata.org/workflows/chapters/3_Metagenome_Reads_QC/',
            'Read-based Taxonomy Classification': 'https://docs.microbiomedata.org/workflows/chapters/2_Read_Based_Taxonomy/index.html',
            'Metagenome Assembly': 'https://docs.microbiomedata.org/workflows/chapters/4_Metagenome_Assembly/index.html',
            'Metagenome Annotation': 'https://docs.microbiomedata.org/workflows/chapters/5_Metagenome_and_Metatranscriptome_Annotation/index.html',
            'Metagenome MAGs': 'https://docs.microbiomedata.org/workflows/chapters/6_Metagenome_Assembled_Genome/index.html'
        },
        bgcolor: '#4F3C80'
    },
}

export const workflowlist = {
    Metatranscriptome: {
        inTutorial: true,
        title: 'Metatranscriptomics',
        name: 'Metatranscriptomics Workflow',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/7_Metatranscriptome_Workflow_Overview/',
        bgcolor: '#4F3C80',
        link: 'https://github.com/microbiomedata/metaT',
        info: 'This workflow is designed to analyze metatranscriptomes.'
    },
    'Metaproteomics': {
        inTutorial: true,
        title: 'Metaproteomics',
        name: 'Metaproteomics Workflow',
        bgcolor: '#4F3C80',
        link: 'https://github.com/microbiomedata/metaPro',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/11_Metaproteomics/index.html',
        info: 'Metaproteomics workflow/pipeline is an end-to-end data processing and analyzing pipeline for studying proteomes i.e studying protein identification and characterization using MS/MS data.'
    },
    EnviroMS: {
        inTutorial: true,
        title: 'Natural Organic Matter',
        name: 'Natural Organic Matter Workflow',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/13_Natural_Organic_Matter/index.html',
        bgcolor: '#4F3C80',
        link: 'https://github.com/microbiomedata/enviroMS',
        info: 'This workflow is for natural organic matter data processing and annotation'
    },
    'virus_plasmid': {
        inTutorial: true,
        title: 'Viruses and Plasmids',
        name: 'Viruses and Plasmids Workflow',
        bgcolor: '#4F3C80',
        doclink: 'https://portal.nersc.gov/genomad/',
        link: 'https://portal.nersc.gov/genomad/',
        info: 'This workflow identifies virus and plasmid sequences in assembled scaffolds using <a href="https://github.com/apcamargo/genomad/" target="_blank" rel="noreferrer">geNomad</a> and estimates the quality of viral genomes with <a href="https://bitbucket.org/berkeleylab/checkv/src/master/" target="_blank" rel="noreferrer">CheckV</a>.'
    },
    ReadsQC: {
        title: 'ReadsQC',
        name: 'ReadsQC Workflow',
        link: 'https://github.com/microbiomedata/ReadsQC',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/3_Metagenome_Reads_QC/',
        info: 'This workflow utilizes the program “rqcfilter2” from BBTools to perform quality control on raw Illumina reads.',
        bulk_file_tip: 'Required',
        bulk_submission_template: '/docs/bulk-submissions/NMDC-EDGE-Metagenomics-ReadsQC-bulk-submission.xlsx',
    },
    ReadbasedAnalysis: {
        title: 'Read-based Taxonomy Classification',
        name: 'Read-based Taxonomy Classification Workflow',
        link: 'https://github.com/microbiomedata/ReadbasedAnalysis',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/2_Read_Based_Taxonomy/index.html',
        info: 'The pipeline takes sequencing files (single- or paired-end) and profiles them using multiple taxonomic classification tools.'
    },
    MetaAssembly: {
        title: 'Metagenome Assembly',
        name: 'Metagenome Assembly Workflow',
        link: 'https://github.com/microbiomedata/metaAssembly',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/4_Metagenome_Assembly/index.html',
        info: 'This workflow takes in paired-end Illumina reads in interleaved format and performs error correction, then reformats the interleaved file into two FASTQ files for downstream tasks using bbcms (BBTools).'
    },
    MetaAnnotation: {
        title: 'Metagenome Annotation',
        name: 'Metagenome Annotation Workflow',
        link: 'https://github.com/microbiomedata/mg_annotation',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/5_Metagenome_and_Metatranscriptome_Annotation/index.html',
        info: 'It takes assembled metagenomes and generates structrual and functional annotations.'
    },
    MetaMAGs: {
        title: 'Metagenome MAGs',
        name: 'Metagenome MAGs Workflow',
        link: 'https://github.com/microbiomedata/metaMAGs',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/6_Metagenome_Assembled_Genome/index.html',
        info: 'This workflow is based on IMG’s metagenome assembled genomes (MAGs) pipeline.'
    },
    'sra2fastq': {
        title: 'Retrieve SRA Data',
        name: 'Retrieve SRA Data Workflow',
        link: 'https://github.com/LANL-Bioinformatics/EDGE_workflows/tree/main/sra2fastq',
        doclink: 'https://github.com/LANL-Bioinformatics/EDGE_workflows/tree/main/sra2fastq',
        info: 'This tool retrieves sequence project in FASTQ files from  NCBI- SRA / EBI - ENA / DDBJ database. Input accession number supports studies(SRP*/ ERP * /DRP*), experiments (SRX*/ERX * /DRX*), samples(SRS * /ERS*/DRS *), runs(SRR * /ERR*/DRR *), or submissions (SRA * /ERA*/DRA *).'
    },
    'Metagenome Pipeline': {
        title: 'Metagenome Pipeline',
        info: 'Run multiple metagenomics workflows: ReadsQC, Read-based Taxonomy Classification, Metagenome Assembly, Viruses and Plasmids, Metagenome Annotation and Metagemone MAGs.',
        bulk_file_tip: 'Required',
        bulk_submission_template: '/docs/bulk-submissions/NMDC-EDGE-Metagenomics-pipeline-bulk-submission.xlsx',
        doclink: 'https://docs.microbiomedata.org/workflows/chapters/1_Metagenome_Workflow_Overview/index.html',
    }
}
