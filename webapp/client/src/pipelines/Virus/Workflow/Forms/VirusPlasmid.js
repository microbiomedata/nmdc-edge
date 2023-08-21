import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse, Input, Button, ButtonGroup
} from 'reactstrap';

import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

import { validFile } from '../../../../common/util';
import FileSelector from '../../../../common/FileSelector';
import MySelect from '../../../../common/MySelect';
import { WarningTooltip, MyTooltip } from '../../../../common/MyTooltip';
import { useForm } from "react-hook-form";
import { Header } from '../../../Common/Forms/CardHeader';
import { defaults, initialVirusPlasmid, workflowInputTips } from '../Defaults';

export function VirusPlasmid(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });
    const [form, setState] = useState({ ...initialVirusPlasmid });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const minVirusHallmarkReg = register("min_virus_hallmark", {
        required: "required, an integer >=0",
        setValueAs: v => parseInt(v),
        min: { value: initialVirusPlasmid.dataRanges['min_virus_hallmark'].min, message: 'Value is less than ' + initialVirusPlasmid.dataRanges['min_virus_hallmark'].min },
        validate: (value) => {
            if (!/^[0-9]+$/.test(value)) {
                return 'Not an integer.';
            }
        }
    });

    const minPlasmidHallmarkReg = register("min_plasmid_hallmark", {
        required: "required, an integer >=0",
        setValueAs: v => parseInt(v),
        min: { value: initialVirusPlasmid.dataRanges['min_plasmid_hallmark'].min, message: 'Value is less than ' + initialVirusPlasmid.dataRanges['min_plasmid_hallmark'].min },
        validate: (value) => {
            if (!/^[0-9]+$/.test(value)) {
                return 'Not an integer.';
            }
        }
    });

    const min_plasmid_hallmarks_short_seqsReg = register("min_plasmid_hallmarks_short_seqs", {
        required: "required, an integer >=0",
        setValueAs: v => parseInt(v),
        min: { value: initialVirusPlasmid.dataRanges['min_plasmid_hallmarks_short_seqs'].min, message: 'Value is less than ' + initialVirusPlasmid.dataRanges['min_plasmid_hallmarks_short_seqs'].min },
        validate: (value) => {
            if (!/^[0-9]+$/.test(value)) {
                return 'Not an integer.';
            }
        }
    });

    const min_virus_hallmarks_short_seqsReg = register("min_virus_hallmarks_short_seqs", {
        required: "required, an integer >=0",
        setValueAs: v => parseInt(v),
        min: { value: initialVirusPlasmid.dataRanges['min_virus_hallmarks_short_seqs'].min, message: 'Value is less than ' + initialVirusPlasmid.dataRanges['min_virus_hallmarks_short_seqs'].min },
        validate: (value) => {
            if (!/^[0-9]+$/.test(value)) {
                return 'Not an integer.';
            }
        }
    });

    const min_plasmid_marker_enrichmentReg = register("min_plasmid_marker_enrichment", {
        required: "required, a float number.",
        setValueAs: v => parseFloat(v),

    });

    const min_virus_marker_enrichmentReg = register("min_virus_marker_enrichment", {
        required: "required, a float number.",
        setValueAs: v => parseFloat(v),

    });

    const max_uscgReg = register("max_uscg", {
        required: "required, an integer >=0",
        setValueAs: v => parseInt(v),
        min: { value: initialVirusPlasmid.dataRanges['max_uscg'].min, message: 'Value is less than ' + initialVirusPlasmid.dataRanges['max_uscg'].min },
        validate: (value) => {
            if (!/^[0-9]+$/.test(value)) {
                return 'Not an integer.';
            }
        }
    });

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

    const handleFastaFileSelection = (filename, type, index, key) => {
        if (!validFile(key)) {
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        setState({
            ...form,
            ['input_fasta']: filename, ['input_fasta_display']: key
        });
        setValue("fasta_hidden", filename, { shouldValidate: true });
        setDoValidation(doValidation + 1);
    }

    const handleOptionSelectChange = selected => {
        Object.keys(form.option).forEach(option => {
            if (option === selected) {
                form.option[option] = true;
            } else {
                form.option[option] = false;
            }
            let values = form.defaults.default;
            if (selected === 'relaxed') {
                values = form.defaults.relaxed;
            } else if (selected === 'conservative') {
                values = form.defaults.conservative;
            }
            form.min_score = values.min_score;
            form.min_plasmid_marker_enrichment = values.min_plasmid_marker_enrichment;
            form.min_virus_marker_enrichment = values.min_virus_marker_enrichment;
            form.min_plasmid_hallmark = values.min_plasmid_hallmark;
            form.min_plasmid_hallmarks_short_seqs = values.min_plasmid_hallmarks_short_seqs;
            form.min_virus_hallmark = values.min_virus_hallmark;
            form.min_virus_hallmarks_short_seqs = values.min_virus_hallmarks_short_seqs;
            form.max_uscg = values.max_uscg;
        });

        setDoValidation(doValidation + 1);
    };

    // set default
    useEffect(() => {
        handleOptionSelectChange('default');
    }, []);// eslint-disable-line react-hooks/exhaustive-deps

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

                if (!errors['fasta_hidden'] && !form.option.custom) {
                    form.validForm = true;
                    form.errMessage = '';
                }
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
                            <MyTooltip id='VirusPlasmid-fasta' text="Input Assembled Fasta File" tooltip={workflowInputTips['virus_plasmid']['fasta_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFastaFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http/https url'}
                                validFile={validFile}
                                dataSources={['upload', 'public', 'globus', 'project']}
                                projectScope={'self+shared'}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Assembly']}
                                fileTypes={['fasta', 'fa', 'fna', 'contigs', 'fasta.gz', 'fa.gz', 'fna.gz', 'contigs.gz', 'fasta.bz2', 'fa.bz2', 'fna.bz2', 'contigs.bz2', 'fasta.xz', 'fa.xz', 'fna.xz', 'contigs.xz']} fieldname={'input_fasta'} viewFile={false} />

                            <input type="hidden" name="fasta_hidden" id="fasta_hidden"
                                value={form['input_fasta']}
                                {...register("fasta_hidden", { required: 'fasta file is required' })} />
                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            Run Option
                        </Col>
                        <Col xs="12" md="9">
                            <MySelect
                                options={initialVirusPlasmid.runOptions}
                                value={initialVirusPlasmid.runOptions[2]}
                                onChange={e => {
                                    handleOptionSelectChange(e.value);
                                }}
                            />
                        </Col>
                    </Row>
                    <br></br>
                    {form.option['custom'] &&
                        <>
                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_score' text="Min geNomad Score" tooltip={workflowInputTips['virus_plasmid']['min_score']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    {form["min_score"]}
                                    <Slider name="min_score"
                                        value={form["min_score"]}
                                        min={initialVirusPlasmid.dataRanges["min_score"].min} max={initialVirusPlasmid.dataRanges["min_score"].max}
                                        step={initialVirusPlasmid.dataRanges["min_score"].step}
                                        onChange={e => setNewState2("min_score", e)}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_plasmid_marker_enrichment' text="Min Plasmid Marker Enrichment" tooltip={workflowInputTips['virus_plasmid']['min_plasmid_marker_enrichment']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_plasmid_marker_enrichment" id="min_plasmid_marker_enrichment" defaultValue={form['min_plasmid_marker_enrichment']}
                                        placeholder={"required, a float number"}
                                        style={errors['min_plasmid_marker_enrichment'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            min_plasmid_marker_enrichmentReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={min_plasmid_marker_enrichmentReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_virus_marker_enrichment' text="Min Virus Marker Enrichment" tooltip={workflowInputTips['virus_plasmid']['min_virus_marker_enrichment']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_virus_marker_enrichment" id="min_virus_marker_enrichment" defaultValue={form['min_virus_marker_enrichment']}
                                        placeholder={"required, a float numbe"}
                                        style={errors['min_virus_marker_enrichment'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            min_virus_marker_enrichmentReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={min_virus_marker_enrichmentReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_plasmid_hallmark' text="Min Plasmid Hallmark" tooltip={workflowInputTips['virus_plasmid']['min_plasmid_hallmark']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_plasmid_hallmark" id="min_plasmid_hallmark" defaultValue={form['min_plasmid_hallmark']}
                                        placeholder={"required, an integer >=0"}
                                        style={errors['min_plasmid_hallmark'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            minPlasmidHallmarkReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={minPlasmidHallmarkReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_plasmid_hallmarks_short_seqs' text="Min Plasmid Hallmarks Short Seqs" tooltip={workflowInputTips['virus_plasmid']['min_plasmid_hallmarks_short_seqs']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_plasmid_hallmarks_short_seqs" id="min_plasmid_hallmarks_short_seqs" defaultValue={form['min_plasmid_hallmarks_short_seqs']}
                                        placeholder={"required, an integer >=0"}
                                        style={errors['min_plasmid_hallmarks_short_seqs'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            min_plasmid_hallmarks_short_seqsReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={min_plasmid_hallmarks_short_seqsReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_virus_hallmark' text=" Min Virus Hallmark" tooltip={workflowInputTips['virus_plasmid']['min_virus_hallmark']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_virus_hallmark" id="min_virus_hallmark" defaultValue={form['min_virus_hallmark']}
                                        placeholder={"required, an integer >=0"}
                                        style={errors['min_virus_hallmark'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            minVirusHallmarkReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={minVirusHallmarkReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>

                            <Row>
                                <Col md="3">
                                    <MyTooltip id='min_virus_hallmarks_short_seqs' text="Min Virus Hallmarks Short Seqs" tooltip={workflowInputTips['virus_plasmid']['min_virus_hallmarks_short_seqs']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="min_virus_hallmarks_short_seqs" id="min_virus_hallmarks_short_seqs" defaultValue={form['min_virus_hallmarks_short_seqs']}
                                        placeholder={"required, an integer >=0"}
                                        style={errors['min_virus_hallmarks_short_seqs'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            min_virus_hallmarks_short_seqsReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={min_virus_hallmarks_short_seqsReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>
                            <Row>
                                <Col md="3">
                                    <MyTooltip id='max_uscg' text="Max USCGs" tooltip={workflowInputTips['virus_plasmid']['max_uscg']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <Input type="number" name="max_uscg" id="max_uscg" defaultValue={form['max_uscg']}
                                        placeholder={"required, an integer >=0"}
                                        style={errors['max_uscg'] ? defaults.inputStyleWarning : defaults.inputStyle}
                                        onChange={(e) => {
                                            max_uscgReg.onChange(e); // method from hook form register
                                            setNewState2(e.target.name, parseInt(e.target.value)); // your method
                                        }}
                                        innerRef={max_uscgReg.ref}
                                    />
                                </Col>
                            </Row>
                            <br></br>
                            <Row>
                                <Col md="3">
                                    <MyTooltip id='score_calibration' text="Score Calibration?" tooltip={workflowInputTips['virus_plasmid']['score_calibration']} showTooltip={true} place="right" />
                                </Col>
                                <Col xs="12" md="9">
                                    <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                        <Button color="outline-primary" onClick={() => {
                                            setNewState2("score_calibration", true)
                                        }}
                                            active={form.score_calibration}>True</Button>
                                        <Button color="outline-primary" onClick={() => {
                                            setNewState2("score_calibration", false)
                                        }}
                                            active={!form.score_calibration}>False</Button>
                                    </ButtonGroup>
                                </Col>
                            </Row>
                            <br></br>
                            {form['score_calibration'] &&
                                <>
                                    <Row>
                                        <Col md="3">
                                            <MyTooltip id='fdr' text="False Discovery Rate" tooltip={workflowInputTips['virus_plasmid']['fdr']} showTooltip={true} place="right" />
                                        </Col>
                                        <Col xs="12" md="9">
                                            {form["fdr"]}
                                            <Slider name="fdr"
                                                value={form["fdr"]}
                                                min={initialVirusPlasmid.dataRanges["fdr"].min} max={initialVirusPlasmid.dataRanges["fdr"].max}
                                                step={initialVirusPlasmid.dataRanges["fdr"].step}
                                                onChange={e => setNewState2("fdr", e)}
                                            />
                                        </Col>
                                    </Row>
                                    <br></br>
                                </>
                            }
                        </>
                    }

                </CardBody>
            </Collapse>
        </Card >
    );
}
