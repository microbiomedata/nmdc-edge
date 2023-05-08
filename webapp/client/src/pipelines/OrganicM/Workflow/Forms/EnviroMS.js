import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse, Button, ButtonGroup,
} from 'reactstrap';
import { Range } from 'rc-slider';
import 'rc-slider/assets/index.css';

import { MyTooltip } from '../../../../common/MyTooltip';
import FileSelector from '../../../../common/FileSelector';
import MySelect from '../../../../common/MySelect';
import { useForm } from "react-hook-form";
import { defaults, initialEnviroMS, EnviroMS_output_type_options, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';
import { FileInputArray } from '../../../Common/Forms/FileInputArray';

export function EnviroMS(props) {
    const enabled = false;
    const { register, control, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });
    //need initial array for workflow selected more than once, otherwise workflows will share same inputs
    const [form, setState] = useState({ ...initialEnviroMS, file_paths: [] });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });

        setDoValidation(doValidation + 1);
    }

    const setRange = (name1, name2, e) => {
        setState({
            ...form,
            [name1]: e[0], [name2]: e[1]
        });

        setDoValidation(doValidation + 1);
    }

    const handleFileSelection = (filename, fieldname) => {
        setNewState2(fieldname, filename);
        setValue(fieldname + "_hidden", filename, { shouldValidate: true });
        setDoValidation(doValidation + 1);
    }

    const updateInputArray = (FileInputs) => {
        form.file_paths = FileInputs.inputFiles;
        form.file_paths_display = FileInputs.inputFilesDisplay;
        form.validInputArray = FileInputs.validForm;
        form.errMessage = FileInputs.errMessage;
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
                if (form.calibrate && errors.calibration_ref_file_path_hidden) {
                    errMessage += errors.calibration_ref_file_path_hidden.message + "<br />";
                }
                if (errors.corems_json_path_hidden) {
                    errMessage += errors.corems_json_path_hidden.message + "<br />";
                }
                if (errMessage === '') {
                    //errors only contains deleted dynamic input hidden errors
                    form.validForm = true;
                }
                form.errMessage = errMessage;
            }
            if (!form.validInputArray) {
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
                    <MyTooltip id='EnviroMS' text="Input Data" tooltip={workflowInputTips['EnviroMS']['txt_tip']} showTooltip={true} place="right" />
                    <FileInputArray fileTypes={['txt', 'csv', 'tsv', 'xlsx', 'raw', 'd']} fileDesc={"mass list file(s)"} filename={props.name} full_name={props.full_name}
                        setParams={updateInputArray} collapseParms={true} dataSources={['upload', 'public']}/>
                    {enabled && <>
                        <Row>
                            <Col md="3">
                                Output Type
                            </Col>
                            <Col xs="12" md="9">
                                <MySelect
                                    defaultValue={EnviroMS_output_type_options[1]}
                                    options={EnviroMS_output_type_options}
                                    onChange={e => {
                                        if (e) {
                                            setNewState2("output_type", e.value)
                                        }
                                    }}
                                    placeholder="Select an output type ..."
                                    isClearable={false}
                                />
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> Calibrate </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("calibrate", true)
                                    }}
                                        active={form.calibrate}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("calibrate", false)
                                    }}
                                        active={!form.calibrate}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        {form.calibrate &&
                            <>
                                <Row>
                                    <Col md="3"> Calibration Ref File </Col>
                                    <Col xs="12" md="9">
                                        <FileSelector onChange={handleFileSelection} dataSources={['upload', 'public']}
                                            fileTypes={['ref']} fieldname={'calibration_ref_file_path'} viewFile={false} />

                                        <input type="hidden" name="calibration_ref_file_path_hidden" id="calibration_ref_file_path_hidden"
                                            value={form['calibration_ref_file_path']}
                                            {...register("calibration_ref_file_path_hidden", { required: 'Clibration ref file is required' })} />
                                    </Col>
                                </Row>
                                <br></br>
                            </>
                        }
                        <Row>
                            <Col md="3"> Corems JSON File </Col>
                            <Col xs="12" md="9">
                                <FileSelector onChange={handleFileSelection} dataSources={['upload', 'public']}
                                    fileTypes={['json']} fieldname={'corems_json_path'} viewFile={false} />

                                <input type="hidden" name="corems_json_path_hidden" id="corems_json_path_hidden"
                                    value={form['corems_json_path']}
                                    {...register("corems_json_path_hidden", { required: 'Corems JSON file is required' })} />
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> Polarity </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("polarity", 'negative')
                                    }}
                                        active={form.polarity === 'negative'}>Negative</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("polarity", 'positive')
                                    }}
                                        active={form.polarity === 'positive'}>Positive</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> Is Centroid </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("is_centroid", true)
                                    }}
                                        active={form.is_centroid}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("is_centroid", false)
                                    }}
                                        active={!form.is_centroid}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3">  Raw File Scan </Col>
                            <Col xs="12" md="9">
                                <Row>
                                    <Col> Start: {form.raw_file_start_scan}</Col>
                                    <Col className="edge-right"> Final: {form.raw_file_final_scan} </Col>
                                </Row>
                                <Range min={1} max={100} step={1} value={[form.raw_file_start_scan, form.raw_file_final_scan]}
                                    onChange={e => {
                                        setRange('raw_file_start_scan', 'raw_file_final_scan', e);
                                    }} allowCross={false} />
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> Plot mz error </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_mz_error", true)
                                    }}
                                        active={form.plot_mz_error}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_mz_error", false)
                                    }}
                                        active={!form.plot_mz_error}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> plot_ms_assigned_unassigned </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_ms_assigned_unassigned", true)
                                    }}
                                        active={form.plot_ms_assigned_unassigned}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_ms_assigned_unassigned", false)
                                    }}
                                        active={!form.plot_ms_assigned_unassigned}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> plot_c_dbe </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_c_dbe", true)
                                    }}
                                        active={form.plot_c_dbe}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_c_dbe", false)
                                    }}
                                        active={!form.plot_c_dbe}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> plot_van_krevelen </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_van_krevelen", true)
                                    }}
                                        active={form.plot_van_krevelen}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_van_krevelen", false)
                                    }}
                                        active={!form.plot_van_krevelen}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> plot_ms_classes </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_ms_classes", true)
                                    }}
                                        active={form.plot_ms_classes}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_ms_classes", false)
                                    }}
                                        active={!form.plot_ms_classes}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                        <Row>
                            <Col md="3"> plot_mz_error_classes </Col>
                            <Col xs="12" md="9">
                                <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_mz_error_classes", true)
                                    }}
                                        active={form.plot_mz_error_classes}>True</Button>
                                    <Button color="outline-primary" onClick={() => {
                                        setNewState2("plot_mz_error_classes", false)
                                    }}
                                        active={!form.plot_mz_error_classes}>False</Button>
                                </ButtonGroup>
                            </Col>
                        </Row>
                        <br></br>
                    </>
                    }

                </CardBody>

            </Collapse>
        </Card >
    );
}
