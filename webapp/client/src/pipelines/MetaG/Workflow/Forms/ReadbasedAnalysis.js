import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import MySelect from '../../../../common/MySelect';
import { WarningTooltip, MyTooltip } from '../../../../common/MyTooltip';
import { useForm } from "react-hook-form";
import { defaults, initialReadbasedAnalysis, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';
import { FastqInput } from '../../../Common/Forms/FastqInput';

export function ReadbasedAnalysis(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });
    //need initial array for workflow selected more than once, otherwise workflows will share same inputs
    const [form] = useState({ ...initialReadbasedAnalysis, fastqPaired: [], fastqSingle: [] });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
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

    const updateFastqInputs = (fastqInputs) => {
        form.fastqPaired = fastqInputs.fastqPaired;
        form.fastqSingle = fastqInputs.fastqSingle;
        form.paired = !fastqInputs.interleaved;
        form.validInputArray = fastqInputs.validForm;
        form.errMessage = fastqInputs.errMessage;
        form.fastqPairedDisplay = fastqInputs.fastqPairedDisplay;
        form.fastqSingleDisplay = fastqInputs.fastqSingleDisplay;
        setDoValidation(doValidation + 1);
    }

    //trigger validation method when input changes
    useEffect(() => {
        //validate form
        trigger().then(result => {
            form.validForm = result;
            if (result) {
                form.errMessage = '';
            } else {
                let errMessage = '';

                if (errors.tool_hidden) {
                    errMessage += errors.tool_hidden.message + "<br />";
                } else {
                    //errors only contains deleted dynamic input hidden errors
                    form.validForm = true;
                }
                form.errMessage = errMessage;
            }
            if(!form.validInputArray) {
                form.validForm = false;
            }
            //force updating parent's inputParams
            props.setParams(form, props.full_name);
        });
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
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
                    <br></br>
                    <MyTooltip id='ReadbasedAnalysis' text="Input Raw Reads" tooltip={workflowInputTips['ReadbasedAnalysis']['fastq_tip']} showTooltip={true} place="right" />
                    <FastqInput projectTypes={['ReadsQC','Retrieve SRA Data']} singleType={'single-end or interleaved'} name={props.name} full_name={props.full_name} setParams={updateFastqInputs} collapseParms={true} paired-input-max={form['paired-input-max']} />
                </CardBody>
            </Collapse>
        </Card >
    );
}
