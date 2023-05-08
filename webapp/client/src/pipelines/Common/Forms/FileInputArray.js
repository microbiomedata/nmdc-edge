import React, { useState, useEffect } from 'react';
import {
    Button, Col, Row,
} from 'reactstrap';

import FileSelector from '../../../common/FileSelector';
import { WarningTooltip } from '../../../common/MyTooltip';
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { defaults, initialFileInputArray } from './Defaults';

export function FileInputArray(props) {
    const { register, control, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });

    const { fields: fileInputFields, append: fileInputAppend, remove: fileInputRemove, } = useFieldArray(
        {
            control,
            name: "fileInput"
        }
    );

    //need initial array for workflow selected more than once, otherwise workflows will share same inputs
    const [form, setState] = useState({...initialFileInputArray});
    const [doValidation, setDoValidation] = useState(0);

    const resetFileInputArray = () => {
        form.inputFiles = [];
        form.inputFilesDisplay = [];
    }

    const handleInputFileSelection = (path, type, index, key) => {
        form.inputFiles[index] = path;
        form.inputFilesDisplay[index] = key;
        setValue("fileInput" + index + "_hidden", path, { shouldValidate: true });

        setDoValidation(doValidation + 1);
    }

    const validateFileInputArrays = () => {
        let valid = true;

        if (form.inputFiles.length === 0) {
            valid = false;
        }

        if (valid) {
            setValue('hidden_files', 'valid', { shouldValidate: true });
        } else {
            setValue('hidden_files', '', { shouldValidate: true });
        }
    }

    //default 1 dataset
    useEffect(() => {
        fileInputAppend({ name: "inputFiles" });
        setState({ ...form, ['inputFiles']: [], ['inputFilesDisplay']: [] });
        setDoValidation(doValidation + 1);
    }, []);// eslint-disable-line react-hooks/exhaustive-deps


    //trigger validation method when input changes
    useEffect(() => {
        //validate inputs
        validateFileInputArrays();
        //validate form
        trigger().then(result => {
            form.validForm = result;
            if (result) {
                form.errMessage = '';
            } else {
                let errMessage = '';
                //check deleted dynamic input hidden 
                if (Object.keys(errors).some(term => term.startsWith('fileInput') && errors[term])) {
                    errMessage += 'File input error';
                }
                if (errors.hidden_files) {
                    errMessage += errors.hidden_files.message;
                }
                if (errMessage === '') {
                    //errors only contains deleted dynamic input hidden errors
                    form.validForm = true;
                }
                form.errMessage = errMessage;
            }
            //force updating parent's inputParams
            props.setParams(form, props.name);
        });
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            <Row>
                <Col md="3">{props.fileDesc}
                    {errors.hidden_files && fileInputFields.length === 0 &&
                        <WarningTooltip id='fileInput' tooltip={errors.hidden_files.message} />
                    }
                </Col>
                <Col xs="12" md="9">
                    {(!props['input-max'] || props['input-max'] > 1) &&
                        <Button size="sm" className="btn-pill" color="outline-primary" onClick={() => {
                            if (props['input-max'] && fileInputFields.length >= props['input-max']) {
                                alert("Only allows " + props['input-max'] + " input data set(s).");
                            } else {
                                fileInputAppend({ name: "fileInput" });
                                setDoValidation(doValidation + 1);
                            }
                        }}>
                            Add file&nbsp; <i className="cui-file"></i>
                        </Button>
                    }
                </Col>
            </Row>
            <br></br>
            {fileInputFields.map((item, index) => (
                <div key={item.id}>
                    <Row>
                        <Col md="3" className="edge-sub-field"> Input file #{index + 1}</Col>
                        <Col xs="12" md="9">
                            <Controller
                                render={({ field: { ref, ...rest }, fieldState }) => (
                                    <FileSelector {...rest} {...fieldState}
                                        dataSources={props.dataSources? props.dataSources: ['upload', 'public', 'globus']}
                                        fileTypes={props.fileTypes} viewFile={false}
                                        fieldname={'fileInput'} index={index} onChange={handleInputFileSelection}
                                    />
                                )}

                                name={`fileInput[${index}]`}
                                control={control}
                            />
                            <input type="hidden" name={`fileInput${index}_hidden`} id={`fileInput${index}_hidden`}
                                value={form.inputFiles[index] ? (form.inputFiles[index] || '') : ''}
                                {...register(`fileInput${index}_hidden`, { required: 'Input file is required.' })} />

                        </Col>
                    </Row>
                    <Row>
                        <Col md="3"></Col>
                        <Col xs="12" md="9">
                            <Button size="sm" className="btn-pill" color="ghost-primary"
                                onClick={() => {
                                    form.inputFiles.splice(index, 1);
                                    form.inputFilesDisplay.splice(index, 1);
                                    fileInputRemove(index);
                                    setDoValidation(doValidation + 1);
                                }}> Remove </Button>
                        </Col>
                    </Row>
                    <br></br>
                </div>
            ))}
            <input type="hidden" name="hidden_files" id="hidden_files"
                {...register("hidden_files", { required: 'Input file is required.' })} />

        </>
    );
}

