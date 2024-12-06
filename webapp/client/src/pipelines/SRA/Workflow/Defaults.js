import { colors } from '../../../common/Colors';
export const defaults = {
  //onSubmit, onBlur, onChange
  form_mode: 'onChange',
  showTooltip: true,
  tooltipPlace: 'right',
  inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
  inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
  { value: 'sra2fastq', label: 'Retrieve SRA Data' },
];

export const workflowInputTips = {
  'sra2fastq': {
    accessions: 'Input SRA accessions (comma separate for > 1 input)',

  },
}

export const initialSra2fastq = {
  validForm: false,
  errMessage: '',
  sraAccessions: '',
}