import React, { useState, useEffect } from 'react';
import {
    Col, Row, Input
} from 'reactstrap';
import { useForm } from "react-hook-form";
import { MyTooltip } from '../../../common/MyTooltip';
import { defaults, initialProject } from './Defaults';

export function Project(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });
    const projNameReg = {
        ...register("proj_name", {
            required: "Project name is required",
            minLength: { value: 3, message: 'At least 3 characters' },
            maxLength: { value: 30, message: 'Max 30 characters exceeded' },
            pattern: { // Validation pattern
                value: /^[a-zA-Z0-9\-_.]+$/,
                message: 'Only alphabets, numbers, dashs, dot and underscore are allowed.'
            }
        })
    };

    const [
        form,
        setState
    ] = useState({ ...initialProject });
    const [doValidation, setDoValidation] = useState(0);

    const setNewState = (e) => {
        setState({
            ...form,
            [e.target.name]: e.target.value
        });
        setDoValidation(doValidation + 1);
    }

    useEffect(() => {
        setState({ ...initialProject });
        setValue('proj_name', '', { shouldValidate: true });
    }, [props.reset]);// eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        //validate form
        trigger().then(result => {
            form.validForm = result;
            if (result) {
                form.errMessage = '';
            } else {
                let errMessage = '';
                if (errors.proj_name) {
                    errMessage += errors.proj_name.message;
                }
                form.errMessage = errMessage;
            }
            //force updating parent's inputParams
            props.setParams(form, props.type);
        });
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            <Row>
                <Col md="3">
                    <MyTooltip id='projectname' text="Project/Run Name" tooltip={initialProject.project_name_tip} showTooltip={true} place="right" />
                </Col>
                <Col xs="12" md="9">
                    <Input type="text" name="proj_name" id="proj_name" defaultValue={form.proj_name}
                        placeholder="(required, at 3 but less than 30 characters)"
                        style={errors.proj_name ? defaults.inputStyleWarning : defaults.inputStyle}
                        onChange={(e) => {
                            projNameReg.onChange(e); // method from hook form register
                            setNewState(e); // your method
                        }}
                        innerRef={projNameReg.ref}
                    />
                    {form.proj_name && errors.proj_name && <p className="edge-form-input-error">{errors.proj_name.message}</p>}
                </Col>
            </Row>
            <br></br>
            <Row>
                <Col md="3"> Description </Col>
                <Col xs="12" md="9">
                    <Input type="text" name="proj_desc" onChange={(e) => setNewState(e)} value={form.proj_desc}
                        placeholder="(optional)"
                        id="proj_desc"
                    />
                </Col>
            </Row>
        </>
    );
}