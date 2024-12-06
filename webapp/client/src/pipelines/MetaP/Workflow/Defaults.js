import { colors } from '../../../common/Colors';
export const defaults = {
    //onSubmit, onBlur, onChange
    form_mode: 'onChange',

    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
    { value: 'Metaproteomics', label: 'Metaproteomics' },
];

export const workflowInputTips = {
    'Metaproteomics': {
        raw_tip: 'RAW MS/MS file, should correspond to fastq input to Metagenome workflow<br />Note: The file size limit for the URL input is 10GB',
        fasta_tip: 'Fasta file, output (nmdc_id_proteins.faa) of a MetagenomeAnnotation workflow<br />Note: The file size limit for the URL input is 10GB',
        gff_tip: 'GFF file, output (nmdc_id_functional_annotation.gff) of a MetagenomeAnnotation workflow<br />Note: The file size limit for the URL input is 10GB',
        thermo_raw :'Does mass spec file come from ThermoFisher instrument?',
        qvalue_threshold: 'Q value for analyzing peptides of interest',
        study: 'name of study from sequencing project, if none put in any name'
    },
}

export const initialMetaP = {

    dataRanges: {
        'qvalue_threshold': { min: 0.01, max: 0.10, step: 0.01 },
    },

    validForm: false,
    errMessage: '',
    input_raw: '',
    input_raw_validInput: false,
    input_raw_display: '',
    input_fasta: '',
    input_fasta_validInput: false,
    input_fasta_display: '',
    input_gff: '',
    input_gff_display: '',
    thermo_raw: true,
    qvalue_threshold: 0.05,
    study:'',
}