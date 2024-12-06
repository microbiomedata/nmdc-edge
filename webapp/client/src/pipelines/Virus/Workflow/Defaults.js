import { colors } from '../../../common/Colors';
export const defaults = {
    //onSubmit, onBlur, onChange
    form_mode: 'onChange',

    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
    { value: 'virus_plasmid', label: 'Viruses and Plasmids' },
];

export const workflowInputTips = {
    'virus_plasmid': {
        fasta_tip: 'virus_plasmid requires an assembled fasta file for input. The workflow will not work correctly with raw reads.<br />Note: The file size limit for the URL input is 10GB',
        min_score: 'Minimum score to flag a sequence as virus or plasmid.',
        min_plasmid_marker_enrichment: 'Minimum allowed value for the plasmid marker enrichment score.',
        min_virus_marker_enrichment: 'Minimum allowed value for the virus marker enrichment score.',
        min_plasmid_hallmark: 'Minimum number of plasmid hallmarks in the identified plasmids.',
        min_plasmid_hallmarks_short_seqs: 'Minimum number of plasmid hallmarks in the identified plasmids that are shorter than 2,500 bp.',
        min_virus_hallmark: 'Minimum number of virus hallmarks in the identified viruses.',
        min_virus_hallmarks_short_seqs: 'Minimum number of virus hallmarks in the identified viruses that are shorter than 2,500 bp.',
        max_uscg: 'Maximum allowed number of universal single copy genes (USCGs) in a virus or a plasmid.',
        score_calibration: 'Assigns sample composition data to estimate the true underlying probabilities.',
        fdr:'Maximum accepted false discovery rate. This option will be ignored if the scores were not calibrated.'
    },
}

export const initialVirusPlasmid = {
    runOptions: [
        { value: 'conservative', label: 'conservative' },
        { value: 'custom', label: 'custom' },
        { value: 'default', label: 'default' },
        { value: 'relaxed', label: 'relaxed' },
    ],
    dataRanges: {
        'min_score': { min: 0, max: 1, step: 0.1 },
        'min_virus_hallmark': { min: 0 },
        'min_plasmid_hallmark': { min: 0 },
        'min_plasmid_hallmarks_short_seqs': { min: 0 },
        'min_virus_hallmarks_short_seqs': { min: 0 },
        'min_plasmid_marker_enrichment': { min: 0 },
        'min_virus_marker_enrichment': { min: 0 },
        'max_uscg': { min: 0 },
        'fdr': { min: 0, max: 1, step: 0.05 },
    },
    defaults: {
        default: {
            'min_score': 0.70,
            'min_plasmid_marker_enrichment': 0.00,
            'min_virus_marker_enrichment': 0.00,
            'min_plasmid_hallmark': 0,
            'min_plasmid_hallmarks_short_seqs': 1,
            'min_virus_hallmark': 0,
            'min_virus_hallmarks_short_seqs': 1,
            'max_uscg': 4,
            "score_calibration": false,
            "fdr":0.10,
        },
        relaxed: {
            'min_score': 0.00,
            'min_plasmid_marker_enrichment': -100.00,
            'min_virus_marker_enrichment': -100.00,
            'min_plasmid_hallmark': 0,
            'min_plasmid_hallmarks_short_seqs': 0,
            'min_virus_hallmark': 0,
            'min_virus_hallmarks_short_seqs': 0,
            'max_uscg': 100,
            "score_calibration": false,
            "fdr":0.10,
        },
        conservative: {
            'min_score': 0.80,
            'min_plasmid_marker_enrichment': 1.50,
            'min_virus_marker_enrichment': 1.50,
            'min_plasmid_hallmark': 1,
            'min_plasmid_hallmarks_short_seqs': 1,
            'min_virus_hallmark': 1,
            'min_virus_hallmarks_short_seqs': 1,
            'max_uscg': 2,
            "score_calibration": false,
            "fdr":0.10,
        },
    },
    validForm: false,
    errMessage: '',
    enabled_modules: {
        "end_to_end": true,
        "marker_classification": false,
        "nn_classification": false
    },
    input_fasta: '',
    input_fasta_validInput: false,
    input_fasta_display: '',
    option: {
        'conservative': false,
        'custom': false,
        'default': true,
        'relaxed': false
    },
    'min_score': 0.70,
    'min_plasmid_marker_enrichment': 0.00,
    'min_virus_marker_enrichment': 0.00,
    'min_plasmid_hallmark': 0,
    'min_plasmid_hallmarks_short_seqs': 1,
    'min_virus_hallmark': 0,
    'min_virus_hallmarks_short_seqs': 1,
    'max_uscg': 4,
    "score_calibration": false,
    "fdr":0.10,
}