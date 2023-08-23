import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse, Button, ButtonGroup, Input
} from 'reactstrap';

import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

import { validFile } from '../../../../common/util';
import FileSelector from '../../../../common/FileSelector';
import { MyTooltip } from '../../../../common/MyTooltip';
import { useForm } from "react-hook-form";
import { Header } from '../../../Common/Forms/CardHeader';
import { defaults, initialMetaP, workflowInputTips } from '../Defaults';

export function Metaproteomics(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });
    const [form, setState] = useState({ ...initialMetaP });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const studyReg = {
        ...register("study", {
            required: "Study name is required"
        })
    };
    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const setNewState = (e) => {
        setState({
            ...form,
            [e.target.name]: e.target.value
        });
        setDoValidation(doValidation + 1);
    }

    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });
        setDoValidation(doValidation + 1);
    }

    const handleRawFileSelection = (filename, type, index, key) => {
        if (!validFile(key)) {
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        setState({
            ...form,
            'input_raw': filename, 'input_raw_display': key
        });
        setValue("raw_hidden", filename, { shouldValidate: true });
        setDoValidation(doValidation + 1);
    }

    const handleFastaFileSelection = (filename, type, index, key) => {
        if (!validFile(key)) {
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        const gffFilename = filename.replace('_proteins.faa', '_functional_annotation.gff');
        const gffKey = key.replace('_proteins.faa', '_functional_annotation.gff');
        setState({
            ...form,
            'input_fasta': filename, 'input_fasta_display': key,
            'input_gff': gffFilename, 'input_gff_display': gffKey
        });
        setValue("fasta_hidden", filename, { shouldValidate: true });
        setDoValidation(doValidation + 1);
    }

    const handleGFFFileSelection = (filename, type, index, key) => {
        setState({
            ...form,
            'input_gff': filename, 'input_gff_display': key
        });
        setValue("gff_hidden", filename, { shouldValidate: true });
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
                let errMessage = 'Input error';

                form.errMessage = errMessage;
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
                            <MyTooltip id='MetaP-raw' text="Input Raw File" tooltip={workflowInputTips['Metaproteomics']['raw_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleRawFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http/https url'}
                                validFile={validFile}
                                dataSources={['upload', 'public', 'globus']}
                                fileTypes={['raw', 'raw.gz']} fieldname={'input_raw'} viewFile={false} />

                            <input type="hidden" name="raw_hidden" id="raw_hidden"
                                value={form['input_raw']}
                                {...register("raw_hidden", { required: 'raw file is required' })} />
                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaP-fasta' text="Input Fasta File" tooltip={workflowInputTips['Metaproteomics']['fasta_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFastaFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http/https url'}
                                validFile={validFile}
                                dataSources={['upload', 'public', 'globus', 'project']}
                                endsWith={true} fileTypes={['_proteins.faa']} fieldname={'input_fasta'} viewFile={false}
                                projectScope={'self+shared'}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Annotation']} />

                            <input type="hidden" name="fasta_hidden" id="fasta_hidden"
                                value={form['input_fasta']}
                                {...register("fasta_hidden", { required: 'fasta file is required' })} />
                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaP-gff' text="Input GFF File" tooltip={workflowInputTips['Metaproteomics']['gff_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <Input style={{ backgroundColor: 'white' }} type="text" name="input_gff" disabled value={form.input_gff_display}
                                placeholder="(Refresh input automatically if the 'Input Fasta File' changes)"
                                id="input_gff"
                            />
                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaP-thermo-raw' text="Thermo Raw?" tooltip={workflowInputTips['Metaproteomics']['thermo_raw']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                <Button color="outline-primary" onClick={() => {
                                    setNewState2("thermo_raw", true)
                                }}
                                    active={form.thermo_raw}>True</Button>
                                <Button color="outline-primary" onClick={() => {
                                    setNewState2("thermo_raw", false)
                                }}
                                    active={!form.thermo_raw}>False</Button>
                            </ButtonGroup>
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaP-qvalue' text="QValue Threshold" tooltip={workflowInputTips['Metaproteomics']['qvalue_threshold']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            {form["qvalue_threshold"]}
                            <Slider name="qvalue_threshold"
                                value={form["qvalue_threshold"]}
                                min={initialMetaP.dataRanges["qvalue_threshold"].min} max={initialMetaP.dataRanges["qvalue_threshold"].max}
                                step={initialMetaP.dataRanges["qvalue_threshold"].step}
                                onChange={e => setNewState2("qvalue_threshold", e)}
                            />
                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaP-study' text="Study" tooltip={workflowInputTips['Metaproteomics']['study']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <Input type="text" name="study" id="study" defaultValue={form.study}
                                style={errors.study ? defaults.inputStyleWarning : defaults.inputStyle}
                                onChange={(e) => {
                                    studyReg.onChange(e); // method from hook form register
                                    setNewState(e); // your method
                                }}
                                innerRef={studyReg.ref}
                            />

                        </Col>
                    </Row>
                    <br></br>

                </CardBody>
            </Collapse>
        </Card >
    );
}
