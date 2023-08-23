import { colors } from '../../../common/Colors';
export const defaults = {
    //onSubmit, onBlur, onChange
    form_mode: 'onChange',

    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const workflowOptions = [
    { value: 'EnviroMS', label: 'EnviroMS' },
];

export const workflowInputTips = {
    EnviroMS: {
        txt_tip: 'Generic mass list in profile and centroid mode (include all delimiters types and Excel formats)<br />Note: The file size limit for the URL input is 10GB'
    }
}

export const workflowlist = {
    EnviroMS: {
        title: 'EnviroMS',
        name: 'EnviroMS Workflow',
        link: 'https://github.com/microbiomedata/enviroMS',
        info: 'EnviroMS is a workflow for natural organic matter data processing and annotation'
    }
}

export const initialEnviroMS = {
    validForm: false,
    errMessage: '',
    validInputArray: false,
    file_paths: [],
    output_type: 'csv',
    calibrate: true,
    calibration_ref_file_path: '',
    corems_json_path: '',
    polarity: 'negative',
    is_centroid: true,
    raw_file_start_scan: 1,
    raw_file_final_scan: 7,
    plot_mz_error: true,
    plot_ms_assigned_unassigned: true,
    plot_c_dbe: true,
    plot_van_krevelen: true,
    plot_ms_classes: true,
    plot_mz_error_classes: true,
    file_paths_display: [],
}

export const EnviroMS_output_type_options = [
    { value: 'pandas', label: 'Pandas data frame (can be saved using pickle, h5, etc)' },
    { value: 'csv', label: 'Text Files (.csv, tab separated .txt, etc)' },
    { value: 'xlsx', label: 'Microsoft Excel (xlsx)' },
    { value: 'json', label: 'Automatic JSON for workflow metadata' },
    { value: 'hdf5', label: 'Self-containing Hierarchical Data Format (.hdf5) including raw data and ime-series data-point' },
];