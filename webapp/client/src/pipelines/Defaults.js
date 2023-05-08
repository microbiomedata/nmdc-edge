export const intro = {
    title: 'Introduction',
    name: 'NMDC EDGE Introduction/Quick Start',
    pdf: '/docs/help/quickStart.pdf',
    video: '/docs/videos/nmdc-edge.mp4',
    bgcolor: '#6A9E5D'
}

export const pipelinelist = {
    MetaG: {
        title: 'Metagenomics',
        name: 'Metagenomics',
        video: {
            'ReadsQC': '/docs/videos/ReadsQC.mp4',
            'Read-based Taxonomy Classification': '/docs/videos/ReadBasedAnalysis.mp4',
            'Metagenome Assembly': '/docs/videos/MetagenomeAssembly.mp4',
            'Metagenome Annotation': '/docs/videos/MetagenomeAnnotation.mp4',
            'Metagenome MAGs': '/docs/videos/MetagenomeMAGs.mp4',
            "Multiple Workflows(pipeline)": '/docs/videos/pipeline.mp4',
        },
        pdf: {
            'ReadsQC': '/docs/help/ReadsQC.pdf',
            'Read-based Taxonomy Classification': '/docs/help/ReadBasedAnalysis.pdf',
            'Metagenome Assembly': '/docs/help/MetagenomeAssembly.pdf',
            'Metagenome Annotation': '/docs/help/MetagenomeAnnotation.pdf',
            'Metagenome MAGs': '/docs/help/MetagenomeMAGs.pdf',
        },
        doclink: {
            'ReadsQC': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/1_RQC_index.html',
            'Read-based Taxonomy Classification': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/2_ReadAnalysis_index.html',
            'Metagenome Assembly': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/3_MetaGAssemly_index.html',
            'Metagenome Annotation': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/4_MetaGAnnotation_index.html',
            'Metagenome MAGs': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/5_MAG_index.html'
        },
        bgcolor: '#40AAE8'
    },
    MetaT: {
        title: 'Metatranscriptomics',
        name: 'Metatranscriptomics',
        video: {
            'Metatranscriptome': '/docs/videos/MetaT.mp4',
        },
        pdf: {
            'Metatranscriptome': '/docs/help/MetaT.pdf',
        },
        doclink: {
            'Metatranscriptome': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/6_MetaT_index.html',
        },
        bgcolor: '#4F3C80'
    },
    MetaP: {
        title: 'Metaproteomics',
        name: 'Metaproteomics',
        bgcolor: '#D8322D'
    },
    MetaB: {
        title: 'Metabolomics',
        name: 'Metabolomics',
        bgcolor: '#ED5339'
    },
    OrganicM: {
        title: 'Organic Matter',
        name: 'Organic Matter',
        pdf: {
            'EnviroMS': '/docs/help/EnviroMS.pdf',
        },
        doclink: {
            'EnviroMS': 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/9_NOM_index.html#',
        },
        bgcolor: '#EA8339'
    },

}
