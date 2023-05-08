import { colors } from '../../../common/Colors';

export const defaults = {
    inputStyle: { borderRadius: '5px', backgroundColor: 'white' },
    inputStyleWarning: { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' },
}

export const initialProject = {
    proj_name: '',
    proj_desc: '',
    validForm: false,
    errMessage: 'Project name required',
}

export const initialConfigFile = {
    use_conf_file: false,
    conf_file_path: '',
    validForm: false,
    errMessage: 'Config file required',
};

export const initialFastqInput = {
    validForm: false,
    errMessage: '',
    fastqPaired: [],
    fastqSingle: [],
    interleaved: true,
    fastqPairedDisplay: [],
    fastqSingleDisplay: []
}

export const initialFileInputArray = {
    validForm: false,
    errMessage: '',
    inputFiles: [],
    inputFilesDisplay: []
}
