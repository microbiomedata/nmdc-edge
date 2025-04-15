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
    Metatranscriptome: {
        fastq_tip: 'Metatranscriptomics requires interleaved data in FASTQ format as the input; the file can be compressed. <br/>Acceptable file formats: .fastq, .fq, .fastq.gz, .fq.gz<br />Note: The file size limit for the URL input is 10GB'
    },
}