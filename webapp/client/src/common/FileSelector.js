import React, { useState, useEffect } from 'react';
import {
    Input, InputGroup, InputGroupAddon,
} from 'reactstrap';
import Fab from '@material-ui/core/Fab';
import ListIcon from '@material-ui/icons/List';
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteForeverIcon from '@material-ui/icons/DeleteForever';
import { colors } from './Colors';
import { FileBrowserDialog, FileViewerDialog, LoaderDialog } from './Dialogs';
import { postData, fetchFile } from './util';

const inputStyle = { borderRadius: '5px', backgroundColor: 'white' };
const inputStyleWarning = { borderRadius: '5px', borderLeftColor: colors.danger, backgroundColor: 'white' };

export const FileSelector = (props) => {
    const [file, setFile] = useState('');
    const [file_path, setFile_path] = useState('');
    const [files_loading, setFiles_loading] = useState(false);
    const [disable_view_file, setDisable_view_file] = useState(true);
    const [disable_input, setDisable_input] = useState(!props.enableInput);
    const [cleanup_input, setCleanup_input] = useState(props.cleanupInput)
    const [view_file, setView_file] = useState(false);
    const [file_content, setFile_content] = useState('');
    const [openFBModal, setOpenFBModal] = useState(false);
    const [files, setFiles] = useState([]);

    const loadFiles = () => {
        setFiles_loading(true);
        const userData = {
            projectTypes: props.projectTypes,
            projectScope: props.projectScope,
            fileTypes: props.fileTypes,
            projectStatuses: props.projectStatuses,
            endsWith: props.endsWith,
        };

        //project files
        var promise1 = new Promise(function (resolve, reject) {
            if (props.dataSources.includes('project')) {
                let serverFiles = postData("/auth-api/user/project/files", userData)
                    .then(data => {
                        //console.log(data)
                        return (data.fileData);
                    }).catch(error => {
                        reject(error);
                    });
                resolve(serverFiles);
            } else {
                resolve([]);
            }
        });

        //uploaded files
        var promise2 = new Promise(function (resolve, reject) {
            if (props.dataSources.includes('upload')) {
                let serverFiles = postData("/auth-api/user/upload/files", userData)
                    .then(data => {
                        return (data.fileData);
                    }).catch(error => {
                        reject(error);
                    });
                resolve(serverFiles);
            } else {
                resolve([]);
            }
        });

        //public files
        var promise3 = new Promise(function (resolve, reject) {
            if (props.dataSources.includes('public')) {
                let serverFiles = postData("/auth-api/user/data/files", userData)
                    .then(data => {
                        return (data.fileData);
                    }).catch(error => {
                        reject(error);
                    });
                resolve(serverFiles);
            } else {
                resolve([]);
            }
        });

        //globus data
        var promise4 = new Promise(function (resolve, reject) {
            if (props.dataSources.includes('globus')) {
                let serverFiles = postData("/auth-api/user/globus/files", userData)
                    .then(data => {
                        return (data.fileData);
                    }).catch(error => {
                        reject(error);
                    });
                resolve(serverFiles);
            } else {
                resolve([]);
            }
        });

        Promise.all([promise1, promise2, promise3, promise4]).then(function (retfiles) {
            let allfiles = [].concat.apply([], retfiles);
            //console.log(allfiles)
            setFiles(allfiles);
            setFiles_loading(false);

            setOpenFBModal(true);
        })
            .catch(error => {
                setFiles_loading(false);

                setOpenFBModal(false);
                alert(error);
            });

    }

    const selectFile = () => {
        loadFiles();
    }

    const handleSelectedFile = (fileKey) => {
        //console.log(fileKey)
        setDisable_input(true)
        setCleanup_input(true)
        setOpenFBModal(false);
        setFile_path(fileKey.path);
        setFile(fileKey.key);
        if (props.viewFile === true) {
            setDisable_view_file(false);
        }

        props.onChange(fileKey.filePath, props.fieldname, props.index, fileKey.key);
    }

    const handleUserInputFile = (filename) => {
        setFile_path(filename);
        setFile(filename);
        if (props.viewFile === true) {
            setDisable_view_file(false);
        }
        props.onChange(filename, props.fieldname, props.index, filename);
    }

    const toggleFBModal = () => {
        setOpenFBModal(!openFBModal);
    }

    const viewFile = () => {
        let url = file_path;
        fetchFile(url)
            .then(data => {
                //console.log("data:", data);
                setFile_content(data);
                setView_file(true);
            })
            .catch((error) => {
                alert(error);
            });;
    }
    const deleteFile = () => {
        setDisable_input(false)
        setCleanup_input(false)
        setFile_path("");
        setFile("");
        props.onChange("", props.fieldname, props.index, "");
    }

    useEffect(() => {
        if (props.file && props.file.autoFill) {
            setDisable_input(true)
            setCleanup_input(true)
            setOpenFBModal(false);
            setFile_path(props.file.path);
            setFile(props.file.key);
            if (props.viewFile === true) {
                setDisable_view_file(false);
            }
        }
    }, [props.file]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            <LoaderDialog loading={files_loading} text="loading..." />
            <FileBrowserDialog isOpen={openFBModal} files={files} title="Select a file" noFilesMessage="No file found."
                handleSelectedFile={handleSelectedFile} toggle={toggleFBModal} />
            <FileViewerDialog type={props.viewFileType} isOpen={view_file} toggle={e => setView_file(!view_file)} title={file_path} src={file_content} />
            <InputGroup>
                <Input style={((props.isOptional && !file) || props.validFile) ? inputStyle : inputStyleWarning} type="text" onChange={(e) => handleUserInputFile(e.target.value)}
                    placeholder={props.placeholder ? props.placeholder : "Select a file"} value={file || ""}
                    disabled={disable_input} />
                <InputGroupAddon addonType="append">
                    <Fab size='small' style={{ marginLeft: 10, color: colors.primary, backgroundColor: 'white', }} >
                        <ListIcon onClick={selectFile} />
                    </Fab>
                    {!disable_view_file &&
                        <Fab size='small' style={{ marginLeft: 10, color: colors.primary, backgroundColor: 'white', }}>
                            <VisibilityIcon onClick={viewFile} />
                        </Fab>
                    }
                    {(cleanup_input && file) &&
                        <Fab size='small' style={{ marginLeft: 10, color: colors.primary, backgroundColor: 'white', }}>
                            <DeleteForeverIcon onClick={deleteFile} />
                        </Fab>
                    }
                </InputGroupAddon>
            </InputGroup>
        </>
    );
}

export default FileSelector;