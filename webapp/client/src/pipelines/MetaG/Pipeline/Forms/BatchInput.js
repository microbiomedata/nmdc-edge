import React, { useState, useEffect } from 'react';
import {
    Button, Col, Row,
} from 'reactstrap';

import { useForm, useFieldArray, Controller } from "react-hook-form";
import { SubprojectInput } from '../../../Common/Forms/SubprojectInput';
import { initialBatchInput } from '../Defaults';


export function BatchInput(props) {
    const { control } = useForm({
    });
    const { fields: BatchInputFields, append: subprojectInputAppend, remove: BatchInputRemovee, } = useFieldArray({
        control,
        name: "BatchInput"
    });

    //need initial array for workflow selected more than once, otherwise workflows will share same inputs
    const [form, setState] = useState({ ...initialBatchInput });
    const [doValidation, setDoValidation] = useState(0);

    const setBatchInput = (params, index) => {
        form.inputs[index] = { ...params };
        setDoValidation(doValidation + 1);
    }

    //default 1 dataset
    useEffect(() => {
        subprojectInputAppend({ name: "BatchInput" });
        setState({ ...form, 'inputs': [] });
        setDoValidation(doValidation + 1);
    }, []);// eslint-disable-line react-hooks/exhaustive-deps


    //trigger validation method when input changes
    useEffect(() => {
        form.validForm = true;
        form.errMessage = '';
        form.inputs.forEach(item => {
            if (!item.validForm) {
                form.validForm = false;
                form.errMessage = item.errMessage;
            }
        });
        if (form.inputs.length === 0) {
            form.validForm = false;
            form.errMessage = 'Input error'
        }
        props.setParams(form, props.name);
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            {BatchInputFields.map((item, index) => (
                <div key={item.id}>
                    <Row>
                        <Col md="2" className="edge-sub-field"> Subproject
                            <br></br>
                            {BatchInputFields.length > 1 &&
                                <Button size="sm" className="btn-pill" color="ghost-primary"
                                    onClick={() => {
                                        form.inputs.splice(index, 1);
                                        BatchInputRemovee(index);
                                        setDoValidation(doValidation + 1);
                                    }}> Delete</Button>
                            }
                        </Col>
                        <Col xs="12" md="10">
                            <Controller
                                render={({ field: { ref, ...rest }, fieldState }) => (<>
                                    <SubprojectInput setProject={setBatchInput} setParams={setBatchInput}
                                        name={`subprojectInput${index}`} id={`subprojectInput${index}`} index={index} />
                                </>
                                )}

                                name={`BatchInput[${index}]`}
                                control={control}
                            />

                        </Col>
                    </Row>
                    <br></br>
                </div>
            ))}

            <Row>
                <Col xs="12" md="12">
                    <center>
                        <Button disabled={BatchInputFields.length >= props.joblimit} size="sm" className="btn-pill" color="outline-primary" onClick={() => {
                            subprojectInputAppend({ name: "BatchInput" });
                            setDoValidation(doValidation + 1);
                        }}>
                            Add Next Input
                        </Button><br></br>
                        {BatchInputFields.length >= props.joblimit &&
                            <span className="pt-3 red-text edge-text-size-small">
                                Note: Couldn't add more inputs to this batch submission because you have reached the maximum active jobs allowed in the 'Job Queue'.
                                <br></br>
                                Please try again after some of your 'running'/'in queue' jobs complete.
                            </span>
                        }
                    </center>
                </Col>
            </Row>
            <br></br>
            <br></br>

        </>
    );
}

