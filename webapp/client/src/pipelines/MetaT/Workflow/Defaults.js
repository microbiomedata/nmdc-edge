import { colors } from '../../../common/Colors';
export const defaults = {
    //onSubmit, onBlur, onChange
    form_mode: 'onChange',

    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
    { value: 'Metatranscriptome', label: 'Metatranscriptomics' },
];

export const workflowInputTips = {
    Metatranscriptomics: {
        fastq_tip: 'Metatranscriptomics requires interleaved data in FASTQ format as the input; the file can be compressed. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
}

export const workflowlist = {
    Metatranscriptomics: {
        title: 'Metatranscriptomics',
        name: 'Metatranscriptomics Workflow',
        img: '/docs/images/Metatranscriptome.png',
        thumbnail: '/docs/images/Metatranscriptome-thumbnail.png',
        link: 'https://github.com/microbiomedata/metaT',
        doclink: 'https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/6_MetaT_index.html',
        info: 'This workflow is designed to analyze metatranscriptomes.'
    },
}

export const initialMetatranscriptomics = {
    validForm: false,
    errMessage: '',
    input_fastq: [],
    'single-input-max': 1,
}