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

export const workflowlist = {
  'sra2fastq': {
    title: 'Retrieve SRA Data',
    name: 'Retrieve SRA Data Workflow',
    // img: '/docs/images/sra2fastq.png',
    // thumbnail: '/docs/images/sra2fastq-thumbnail.png',
    link: 'https://github.com/LANL-Bioinformatics/EDGE_workflows/tree/main/sra2fastq',
    doclink: 'https://github.com/LANL-Bioinformatics/EDGE_workflows/tree/main/sra2fastq',
    info: 'This tool retrieves sequence project in FASTQ files from  NCBI- SRA / EBI - ENA / DDBJ database. Input accession number supports studies(SRP*/ ERP * /DRP*), experiments (SRX*/ERX * /DRX*), samples(SRS * /ERS*/DRS *), runs(SRR * /ERR*/DRR *), or submissions (SRA * /ERA*/DRA *).'
  },
}


export const initialSra2fastq = {
  validForm: false,
  errMessage: '',
  sraAccessions: '',
}