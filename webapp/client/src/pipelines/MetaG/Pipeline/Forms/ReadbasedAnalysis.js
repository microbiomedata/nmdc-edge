import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import MySelect from '../../../../common/MySelect';
import { WarningTooltip } from '../../../../common/MyTooltip';
import { useForm } from "react-hook-form";
import { defaults } from '../../../Common/Forms/Defaults';
import { initialReadbasedAnalysis } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';

export function ReadbasedAnalysis(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });

    const [form, setState] = useState({...initialReadbasedAnalysis});
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });

        setDoValidation(doValidation + 1);
    }

    const setOnoff = (stats) => {
        setNewState2("paramsOn", stats);
    }

    const toggleParms = () => {
        if (form.paramsOn) {
            setCollapseParms(!collapseParms);
        }
    }

    const handleToolSelectChange = selected => {
        let tools = [];
        if (selected) {
            tools = selected.map(item => {
                return item.value;
            });
        }

        if (tools.length === 0) {
            setValue('tool_hidden', '', { shouldValidate: true });
        } else {
            setValue('tool_hidden', 'valid', { shouldValidate: true });
        }
        Object.keys(form.enabled_tools).forEach(tool => {
            if (tools.includes(tool)) {
                form.enabled_tools[tool] = true;
            } else {
                form.enabled_tools[tool] = false;
            }
        });

        setDoValidation(doValidation + 1);
    };

    useEffect(() => {
        //select all tools as default
        Object.keys(form.enabled_tools).forEach(tool => {
            form.enabled_tools[tool] = true;
        });
        setValue('tool_hidden', 'valid', { shouldValidate: true });
    }, []);// eslint-disable-line react-hooks/exhaustive-deps

    //trigger validation method when input changes
    useEffect(() => {
        if (!form.paramsOn) {
            form.validForm = true;
            form.errMessage = '';
            //force updating parent's inputParams
            props.setParams(form, props.name);
        } else {
            //validate form
            trigger().then(result => {
                form.validForm = result;
                if (result) {
                    form.errMessage = '';
                } else {
                    let errMessage = '';

                    if (errors.tool_hidden) {
                        errMessage += errors.tool_hidden.message + "<br />";
                    }
                    if (errMessage !== '') {
                        errMessage = "<br /><div class='edge-form-input-error'>Readbased Analysis</div>" + errMessage;
                    } else {
                        //errors only contains deleted dynamic input hidden errors
                        form.validForm = true;
                    }
                    form.errMessage = errMessage;
                }
                //force updating parent's inputParams
                props.setParams(form, props.name);
            });
        }
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps


    return (
        <Card className='workflow-card'>

            <Header toggle={true} toggleParms={toggleParms} title={props.full_name} collapseParms={collapseParms}
                onoff={true} setOnoff={setOnoff} setCollapseParms={setCollapseParms} paramsOn={form.paramsOn} />
            <Collapse isOpen={!collapseParms} id="collapseParameters">
                <CardBody>

                    <Row>
                        <Col md="3">
                            Select Analysis Tool(s)
                            {errors["tool_hidden"] &&
                                <WarningTooltip id='readbasedAnalysisTools' tooltip={errors["tool_hidden"].message} />
                            }
                        </Col>
                        <Col xs="12" md="9">
                            <MySelect
                                isMulti={true}
                                placeholder={'Select tool(s)...'}
                                options={initialReadbasedAnalysis.tool_options}
                                value={initialReadbasedAnalysis.tool_options}
                                selectAll={false}
                                checkbox={true}
                                closeMenuOnSelect={false}
                                hideSelectedOptions={false}
                                onChange={handleToolSelectChange}
                            />
                            <input type="hidden" name={"tool_hidden"} id={"tool_hidden"}
                                {...register("tool_hidden", { required: 'At least one analysis tool is required.' })} />
                        </Col>
                    </Row>
                </CardBody>
            </Collapse>
        </Card>
    );
}

