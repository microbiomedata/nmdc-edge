import React, { useState, useEffect } from 'react';
import {
    Button, ButtonGroup, Col, Row,
} from 'reactstrap';

import { validFile } from '../../../common/util';
import FileSelector from '../../../common/FileSelector';
import { WarningTooltip } from '../../../common/MyTooltip';
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { defaults, initialFastqInput } from './Defaults';

export function FastqInput(props) {
    const { register, control, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });

    const { fields: fastqPairedFields, append: fastqPairedAppend, remove: fastqPairedRemove, } = useFieldArray(
        {
            control,
            name: "fastqPaired"
        }
    );
    const { fields: fastqSingleFields, append: fastqSingleAppend, remove: fastqSingleRemove, } = useFieldArray(
        {
            control,
            name: "fastqSingle"
        }
    );

    //need initial array for workflow selected more than once, otherwise workflows will share same inputs
    const [form, setState] = useState({ ...initialFastqInput });
    const [collapseParms, setCollapseParms] = useState(props.collapseParms);
    const [doValidation, setDoValidation] = useState(0);
    const [singleType, setSingleType] = useState("interleaved");

    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });

        setDoValidation(doValidation + 1);
    }

    const resetFastqInput = () => {
        form.fastqPaired = [];
        form.fastqSingle = [];
        form.fastqPairedDisplay = [];
        form.fastqSingleDisplay = [];
    }

    const handleFastqFileSelection = (path, type, index, key) => {
        if(!validFile(key)) {
            form.validForm = false;
            props.setParams(form, props.name);
            return;
        }
        if (type === 'fastqPaired1') {
            if (form.fastqPaired[index]) {
                form.fastqPaired[index].fq1 = path;
                form.fastqPairedDisplay[index].fq1 = key;
            } else {
                form.fastqPaired[index] = { fq1: path };
                form.fastqPairedDisplay[index] = { fq1: key };
            }
            setValue("fastqPaired" + index + "_fq1_hidden", path, { shouldValidate: true });
        } else if (type === 'fastqPaired2') {
            if (form.fastqPaired[index]) {
                form.fastqPaired[index].fq2 = path;
                form.fastqPairedDisplay[index].fq2 = key;
            } else {
                form.fastqPaired[index] = { fq2: path };
                form.fastqPairedDisplay[index] = { fq2: key };
            }
            setValue("fastqPaired" + index + "_fq2_hidden", path, { shouldValidate: true });
        } else if (type === 'fastqSingle') {
            form.fastqSingle[index] = path;
            form.fastqSingleDisplay[index] = key;
            setValue("fastqSingle" + index + "_fq_hidden", path, { shouldValidate: true });
        }

        setDoValidation(doValidation + 1);
    }

    const validateFastqInputs = () => {
        let valid = true;

        if (!form.interleaved) {
            if (form.fastqPaired.length === 0) {
                valid = false;
            }
        } else {
            if (form.fastqSingle.length === 0) {
                valid = false;
            }
        }

        if (valid) {
            setValue('hidden_fastq', 'valid', { shouldValidate: true });
        } else {
            setValue('hidden_fastq', '', { shouldValidate: true });
        }
    }

    //default 1 dataset
    useEffect(() => {
        fastqSingleAppend({ name: "fastqSingle" });
        fastqPairedAppend({ name: "fastqPaired" });
        setState({ ...form, ['fastqPaired']: [], ['fastqSingle']: [], ['fastqPairedDisplay']: [], ['fastqSingleDisplay']: [] });
        setDoValidation(doValidation + 1);
    }, []);// eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (props.singleType) {
            setSingleType(props.singleType);
        } else {
            setSingleType("interleaved");
        }
    }, [props.singleType]);

    //trigger validation method when input changes
    useEffect(() => {
        //validate fastq data inputs
        validateFastqInputs();
        //validate form
        trigger().then(result => {
            form.validForm = result;
            if (result) {
                form.errMessage = '';
            } else {
                let errMessage = '';
                //check deleted dynamic input hidden 
                if (Object.keys(errors).some(term => term.startsWith('fastq') && errors[term])) {
                    errMessage += 'Fastq input error<br />';
                }
                if (errors.hidden_fastq) {
                    errMessage += errors.hidden_fastq.message + "<br />";
                }
                if (errMessage !== '') {
                    errMessage = "<br /><div class='edge-form-input-error'>Metagenome Inputs</div>" + errMessage;
                } else {
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
            {!props.interleavedOnly &&
                <>
                    <Row>
                        <Col md="3"> Is {singleType}? </Col>
                        <Col xs="12" md="9">
                            <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                <Button color="outline-primary" onClick={() => {
                                    resetFastqInput();
                                    setNewState2("interleaved", true)
                                }}
                                    active={form.interleaved}>Yes</Button>
                                <Button color="outline-primary" onClick={() => {
                                    resetFastqInput();
                                    setNewState2("interleaved", false)
                                }}
                                    active={!form.interleaved}>No</Button>
                            </ButtonGroup>
                        </Col>
                    </Row>
                    <br></br>
                </>
            }

            {form.interleaved &&
                <>
                    <Row>
                        <Col md="3">Input {singleType} fastq
                            {errors.hidden_fastq && fastqSingleFields.length === 0 &&
                                <WarningTooltip id='InputsInputFastq' tooltip={errors.hidden_fastq.message} />
                            }
                        </Col>
                        <Col xs="12" md="9">
                            {(!props['single-input-max'] || props['single-input-max'] > 1) &&
                                <Button size="sm" className="btn-pill" color="outline-primary" onClick={() => {
                                    if (props['single-input-max'] && fastqSingleFields.length >= props['single-input-max']) {
                                        alert("Only allows " + props['single-input-max'] + " " + singleType + " input data set(s).");
                                    } else {
                                        fastqSingleAppend({ name: "fastqSingle" });
                                        setDoValidation(doValidation + 1);
                                    }
                                }}>
                                    Add {singleType} fastq&nbsp; <i className="cui-file"></i>
                                </Button>
                            }
                        </Col>
                    </Row>
                    <br></br>
                    {fastqSingleFields.map((item, index) => (
                        <div key={item.id}>
                            <Row>
                                <Col md="3" className="edge-sub-field"> {singleType} FASTQ #{index + 1}</Col>
                                <Col xs="12" md="9">
                                    <Controller
                                        render={({ field: { ref, ...rest }, fieldState }) => (
                                            <FileSelector {...rest} {...fieldState}
                                                enableInput={true}
                                                placeholder={'Select a file or enter a file http/https url'}
                                                validFile={validFile}
                                                dataSources={props.dataSources ? props.dataSources : ['project', 'upload', 'public', 'globus']}
                                                fileTypes={['fastq', 'fq', 'fastq.gz', 'fq.gz']}
                                                projectTypes={props.projectTypes ? props.projectTypes : null}
                                                viewFile={false}
                                                fieldname={'fastqSingle'} index={index} onChange={handleFastqFileSelection}
                                            />
                                        )}

                                        name={`fastqSingle[${index}].fq`}
                                        control={control}
                                    />
                                    <input type="hidden" name={`fastqSingle${index}_fq_hidden`} id={`fastqSingle${index}_fq_hidden`}
                                        value={form.fastqSingle[index] ? (form.fastqSingle[index] || '') : ''}
                                        {...register(`fastqSingle${index}_fq_hidden`, { required: 'Fastq file is required.' })} />

                                </Col>
                            </Row>
                            {(!props['single-input-max'] || props['single-input-max'] > 1) &&
                                <Row>
                                    <Col md="3"></Col>
                                    <Col xs="12" md="9">
                                        <Button size="sm" className="btn-pill" color="ghost-primary"
                                            onClick={() => {
                                                form.fastqSingle.splice(index, 1);
                                                form.fastqSingleDisplay.splice(index, 1);
                                                fastqSingleRemove(index);
                                                setDoValidation(doValidation + 1);
                                            }}> Remove </Button>
                                    </Col>
                                </Row>
                            }
                            <br></br>
                        </div>
                    ))}

                </>
            }
            {!form.interleaved &&
                <>
                    <Row>
                        <Col md="3">Input paired fastq
                            {errors.hidden_fastq && fastqPairedFields.length === 0 &&
                                <WarningTooltip id='InputsInputFastq' tooltip={errors.hidden_fastq.message} />
                            }
                        </Col>
                        <Col xs="12" md="9">
                            {(!props['paired-input-max'] || props['paired-input-max'] > 1) &&
                                <Button size="sm" className="btn-pill" color="outline-primary" onClick={() => {
                                    if (props['paired-input-max'] && fastqPairedFields.length >= props['paired-input-max']) {
                                        alert("Only allows " + props['paired-input-max'] + " paired-end input data set(s).");
                                    } else {
                                        fastqPairedAppend({ name: "fastqPaired" });
                                        setDoValidation(doValidation + 1);
                                    }
                                }}>
                                    Add paired-end fastq&nbsp; <i className="cui-file"></i>
                                </Button>
                            }
                        </Col>
                    </Row>
                    <br></br>

                    {fastqPairedFields.map((item, index) => (
                        <div key={item.id}>
                            <Row>
                                <Col md="3" className="edge-sub-field"> Pair-1 FASTQ #{index + 1}</Col>
                                <Col xs="12" md="9">
                                    <Controller
                                        render={({ field: { ref, ...rest }, fieldState }) => (
                                            <FileSelector {...rest} {...fieldState}
                                                enableInput={true}
                                                placeholder={'Select a file or enter a file http/https url'}
                                                validFile={validFile}
                                                dataSources={props.dataSources ? props.dataSources : ['project', 'upload', 'public', 'globus']}
                                                fileTypes={['fastq', 'fq', 'fastq.gz', 'fq.gz']} viewFile={false}
                                                projectTypes={props.projectTypes ? props.projectTypes : null}
                                                fieldname={'fastqPaired1'} index={index} onChange={handleFastqFileSelection}
                                            />
                                        )}
                                        name={`fastqPaired[${index}].fq1`}
                                        control={control}
                                    />
                                    <input type="hidden" name={`fastqPaired${index}_fq1_hidden`} id={`fastqPaired${index}_fq1_hidden`}
                                        value={form.fastqPaired[index] ? (form.fastqPaired[index].fq1 || '') : ''}
                                        {...register(`fastqPaired${index}_fq1_hidden`, { required: 'Fastq pair-1 file is required.' })} />

                                </Col>
                            </Row>
                            <br></br>
                            <Row>
                                <Col md="3" className="edge-sub-field"> Pair-2 FASTQ #{index + 1}</Col>
                                <Col xs="12" md="9">
                                    <Controller
                                        render={({ field: { ref, ...rest }, fieldState }) => (
                                            <FileSelector {...rest} {...fieldState}
                                                enableInput={true}
                                                placeholder={'Select a file or enter a file http/https url'}
                                                validFile={validFile}
                                                dataSources={props.dataSources ? props.dataSources : ['project', 'upload', 'public', 'globus']}
                                                fileTypes={['fastq', 'fq', 'fastq.gz', 'fq.gz']} viewFile={false}
                                                projectTypes={props.projectTypes ? props.projectTypes : null}
                                                fieldname={'fastqPaired2'} index={index} onChange={handleFastqFileSelection}
                                            />
                                        )}
                                        name={`fastqPaired[${index}].fq2`}
                                        control={control}
                                    />
                                    <input type="hidden" name={`fastqPaired${index}_fq2_hidden`} id={`fastqPaired${index}_fq2_hidden`}
                                        value={form.fastqPaired[index] ? (form.fastqPaired[index].fq2 || '') : ''}
                                        {...register(`fastqPaired${index}_fq2_hidden`, { required: 'Fastq pair-2 file is required.' })} />

                                </Col>
                            </Row>
                            {(!props['paired-input-max'] || props['paired-input-max'] > 1) &&
                                <Row>
                                    <Col md="3"></Col>
                                    <Col xs="12" md="9">
                                        <Button size="sm" className="btn-pill" color="ghost-primary"
                                            onClick={() => {
                                                form.fastqPaired.splice(index, 1);
                                                form.fastqPairedDisplay.splice(index, 1);
                                                fastqPairedRemove(index);
                                                setDoValidation(doValidation + 1);
                                            }}> Remove </Button>
                                    </Col>
                                </Row>
                            }
                            <br></br>
                        </div>
                    ))}
                </>
            }
            <input type="hidden" name="hidden_fastq" id="hidden_fastq"
                {...register("hidden_fastq", { required: 'Fastq file is required.' })} />

        </>
    );
}

