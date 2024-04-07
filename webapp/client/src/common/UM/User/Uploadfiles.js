import React, { useState, useEffect } from 'react';
import { Col, Row, } from 'reactstrap';
import 'react-dropzone-uploader/dist/styles.css'
import Dropzone from 'react-dropzone-uploader';
import { ToastContainer } from 'react-toastify';
import { notify, formatFileSize, getData, postData, getFileExtension } from "../../util";
import 'react-toastify/dist/ReactToastify.css';

import { LoaderDialog } from "../../Dialogs";
import config from "../../../config";

function Uploadfiles(props) {
    const [submitting, setSubmitting] = useState(false);
    const [uploadedSize, setUploadedSize] = useState(0);
    const [uploadingSize, setUploadingSize] = useState(0);
    const [maxStorageSizeBytes, setMaxStorageSizeBytes] = useState(0);
    const [maxFileSizeBytes, setMaxFileSizeBytes] = useState(0);
    const [daysKept, setDaysKept] = useState(0);

    const allowedExtensions = config.UPLOADS.ALLOWED_FILE_EXTENSIONS;

    useEffect(() => {
        //get upload info
        getData("/auth-api/user/upload/info")
            .then(data => {
                setUploadedSize(data.uploadedSize);
                setMaxStorageSizeBytes(data.maxStorageSizeBytes);
                setMaxFileSizeBytes(data.maxFileSizeBytes);
                setDaysKept(data.daysKept);
            })
            .catch(err => {
                alert(err);
            });
    }, [submitting]);

    const notValidFileExtension = (file) => {
        const ext = getFileExtension(file.meta.name);
        return !allowedExtensions.includes(ext);
    }

    const validateFile = (file) => {
        if (file.meta.size === 0) {
            return true;
        }
        if (notValidFileExtension(file)) {
            return true;
        }
        return false;
    }

    // called every time a file's `status` changes
    const handleChangeStatus = ({ meta }, status, allFiles) => {
        //console.log(meta, status, allFiles)
        let deletFile = false;

        if (status === 'error_file_size') {
            alert(meta.name + ": File too big");
            deletFile = true;
        } else if (status === 'error_validation') {
            alert(meta.name + ": Wrong file extension or Empty file");
            deletFile = true;
        } else if (status === 'removed') {
            setUploadingSize(uploadingSize - meta.size);
        } else if (status === 'done') {
        } else {
            setUploadingSize(uploadingSize + meta.size);
            //check duplicate
            allFiles.forEach(f => {
                if (f.meta.id !== meta.id && f.meta.name === meta.name && f.meta.size === meta.size &&
                    f.meta.type === meta.type && f.meta.lastModifiedDate === meta.lastModifiedDate) {
                    alert(meta.name + ": File is already in the uploading list");
                    deletFile = true;
                }
            });
        }

        if (deletFile) {
            allFiles.forEach(f => {
                if (f.meta.id === meta.id) {
                    f.remove();
                }
            });
        }
    }

    // receives array of files that are done uploading when submit button is clicked
    const handleSubmit = (files, allFiles) => {
        setSubmitting(true);
        //check storage space
        if (uploadedSize + uploadingSize > maxStorageSizeBytes) {
            alert("Storage limit exceeded. Please remove file(s) from your uploading list or delete old uploaded file(s) from the server.");
            setSubmitting(false);
            return;
        }

        //upload files
        let promises = [];
        for (var i = 0; i < files.length; i++) {
            let curr = files[i];
            promises.push(new Promise(function (resolve, reject) {
                let formData = new FormData();
                formData.append('file', curr.file)
                formData.set("name", curr.meta.name);
                formData.set("type", getFileExtension(curr.meta.name));
                formData.set("size", curr.meta.size);

                const url = "/auth-api/user/upload/add";
                postData(url, formData, {
                    headers: {
                        "Content-type": "multipart/form-data",
                    },
                }).then(response => {
                    resolve("Upload " + curr.meta.name + " successfully!")
                }).catch(error => {
                    resolve("Upload " + curr.meta.name + " failed! " + error);
                });
            })
            );
        }

        Promise.all(promises)
            .then(response => {
                allFiles.forEach(f => f.remove())
                response.forEach(e => {
                    if (e.includes("failed")) {
                        notify("error", e);
                    } else {
                        notify("success", e);
                    }
                });
                setSubmitting(false);
                props.reloadTableData();
            })
            .catch(error => {
                alert(error);
                setSubmitting(false);
            });
    }

    return (
        <>
            <LoaderDialog loading={submitting} text="Uploading..." />
            <ToastContainer />
            <Row className="justify-content-center">
                <Col xs="12" md="10">
                    <div className="clearfix">
                        <h4 className="pt-3">Upload Files</h4>
                        <span className="edge-text-font">
                            Max single file size is {formatFileSize(maxFileSizeBytes)}. Max server storage space is {formatFileSize(maxStorageSizeBytes)}.
                            Files will be kept for {daysKept} days.
                        </span>
                        <br></br>
                        Allowed file extensions are: {allowedExtensions.join(", ")}
                        <br></br><br></br>
                        Storage space usage: {formatFileSize(uploadedSize)}/{formatFileSize(maxStorageSizeBytes)}
                        <br></br>
                        Uploading size: {formatFileSize(uploadingSize)}
                        <Dropzone
                            onChangeStatus={handleChangeStatus}
                            onSubmit={handleSubmit}
                            accept="*"
                            autoUpload={false}
                            maxSizeBytes={maxFileSizeBytes}
                            validate={validateFile}
                        />

                    </div>
                </Col>
            </Row>
        </>
    );
}

export default Uploadfiles;