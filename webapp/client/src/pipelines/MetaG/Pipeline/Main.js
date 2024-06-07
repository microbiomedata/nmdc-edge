import React, { useState, useEffect } from 'react';
import {
    Button, Form, Row, Col
} from 'reactstrap';

import { getData, postData, notify } from '../../../common/util';
import { LoaderDialog, MessageDialog } from '../../../common/Dialogs';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { Project } from '../../Common/Forms/Project';
import { ReadbasedAnalysis } from './Forms/ReadbasedAnalysis';
import { MetaAnnotation } from './Forms/MetaAnnotation';
import { VirusPlasmid } from './Forms/VirusPlasmid';
import { MetaAssembly } from './Forms/MetaAssembly';
import { MetaMAGs } from './Forms/MetaMAGs';
import { ReadsQC } from './Forms/ReadsQC';
import { Input } from './Input';
import { initialFastqInput } from '../../Common/Forms/Defaults';
import { workflowlist, initialReadsQC, initialReadbasedAnalysis, initialMetaAssembly, initialVirusPlasmid, initialMetaAnnotation, initialMetaMAGs } from './Defaults';

function Main(props) {
    const [openDialog, setOpenDialog] = useState(false);
    const [disabled, setDisabled] = useState(false);
    const [sysMsg, setSysMsg] = useState();
    const [submitting, setSubmitting] = useState(false);
    const [requestSubmit, setRequestSubmit] = useState(false);
    const [projectParams, setProjectParams] = useState();
    const [inputsParams, setInputsParams] = useState({ ...initialFastqInput });

    const [workflows] = useState({
        "ReadsQC": { ...initialReadsQC },
        "ReadbasedAnalysis": { ...initialReadbasedAnalysis },
        "MetaAssembly": { ...initialMetaAssembly },
        "virus_plasmid": { ...initialVirusPlasmid },
        "MetaAnnotation": { ...initialMetaAnnotation },
        "MetaMAGs": { ...initialMetaMAGs }
    });
    const [doValidation, setDoValidation] = useState(0);
    const [metaAssembly_onoff, setmetaAssembly_onoff] = useState({ ...initialMetaAssembly.paramsOn });
    const [metaMAGs_onoff, setMetaMAGs_onoff] = useState({ ...initialMetaMAGs.paramsOn });

    //callback function for child component
    const setProject = (params) => {
        //console.log("main project:", params)
        setProjectParams(params);
        setDoValidation(doValidation + 1);
    }
    //callback function for child component
    const setInputs = (params) => {
        //console.log("setInputs", params)
        setInputsParams(params);
        setDoValidation(doValidation + 1);
    }
    const setWorkflowParams = (params, workflowName) => {
        //console.log("setworkflow", workflowName, params)
        //setWorkflows({ ...workflows, [workflowName]: params });
        workflows[workflowName] = params;
        //set downstream paramsOn values
        if (workflowName === "MetaAssembly") {
            if (params.paramsOn) {
                setmetaAssembly_onoff(true);
            } else {
                setmetaAssembly_onoff(false);
            }
        } else if (workflowName === "MetaAnnotation") {
            if (params.paramsOn) {
                setMetaMAGs_onoff(true);
            } else {
                setMetaMAGs_onoff(false);
            }
        } else {
            setDoValidation(doValidation + 1);
        }
    }

    const closeMsgModal = () => {
        setOpenDialog(false);
    }
    //submit button clicked
    const onSubmit = () => {
        let formData = new FormData();

        formData.append('pipeline', "Metagenome Pipeline");
        formData.append('project', JSON.stringify({ name: projectParams.proj_name, desc: projectParams.proj_desc }));

        let inputDisplay = {};
        inputDisplay.type = "Metagenome | Run Multiple Workflows";
        inputDisplay.input = {};
        inputDisplay.input['Input Raw Reads'] = {};
        let myInputs = {};
        if (inputsParams.interleaved) {
            myInputs.interleaved = true;
            myInputs.fastqs = inputsParams.fastqSingle;
            inputDisplay.input['Input Raw Reads'].interleaved = true;
            inputDisplay.input['Input Raw Reads'].fastqs = inputsParams.fastqSingleDisplay;
        } else {
            myInputs.interleaved = false;
            myInputs.fastqs = inputsParams.fastqPaired;
            inputDisplay.input['Input Raw Reads'].interleaved = false;
            inputDisplay.input['Input Raw Reads'].fastqs = inputsParams.fastqPairedDisplay;
        }
        formData.append('inputs', JSON.stringify(myInputs));
        //console.log(workflows)
        let workflowParams = [];
        Object.keys(workflowlist).forEach((item, index) => {
            let myWorkflow = {};
            myWorkflow.name = item;

            inputDisplay.input[workflowlist[item].name] = {};
            if (workflows[item].paramsOn) {
                inputDisplay.input[workflowlist[item].name]['On/Off'] = 'On';
            } else {
                inputDisplay.input[workflowlist[item].name]['On/Off'] = 'Off';
            }

            if (['ReadsQC', 'MetaAssembly', 'virus_plasmid', 'MetaAnnotation'].includes(item)) {
                myWorkflow.paramsOn = workflows[item].paramsOn;
                workflowParams.push(myWorkflow);

            } else if (item === 'ReadbasedAnalysis') {
                myWorkflow.paramsOn = workflows[item].paramsOn;
                myWorkflow.enabled_tools = workflows[item].enabled_tools;
                workflowParams.push(myWorkflow);

            } else if (item === 'MetaMAGs') {
                myWorkflow.paramsOn = workflows[item].paramsOn;
                myWorkflow.input_map = workflows[item].input_map;
                myWorkflow.input_domain = workflows[item].input_domain;
                workflowParams.push(myWorkflow);
                if (workflows[item].paramsOn) {
                    inputDisplay.input[workflowlist[item].name]['Input Map File'] = workflows[item].input_map_display;
                    inputDisplay.input[workflowlist[item].name]['Input Domain File'] = workflows[item].input_domain_display;
                }

            }
        });
        formData.append('workflows', JSON.stringify(workflowParams));
        formData.append('inputDisplay', JSON.stringify(inputDisplay));

        //console.log("formdata", JSON.stringify(workflowParams))
        postData("/auth-api/user/project/add", formData)
            .then(data => {
                notify("success", "Your workflow request was submitted successfully!", 2000);
                setTimeout(() => props.history.push("/user/projectlist"), 2000);
            }
            ).catch(error => {
                setSubmitting(false);
                alert(error);
            });
    }

    useEffect(() => {
        //console.log("inputs", inputsParams)
        //console.log("workflows", workflows)
        setRequestSubmit(true);
        if (projectParams && !projectParams.validForm) {
            setRequestSubmit(false);
        }
        if (inputsParams && !inputsParams.validForm) {
            setRequestSubmit(false);
        }

        let ons = 0;
        Object.keys(workflowlist).forEach((item, index) => {
            if (workflows[item] && !workflows[item].validForm) {
                setRequestSubmit(false);
            }
            if (workflows[item] && workflows[item].paramsOn) {
                ons++;
            }
        });

        //check if all workflows are off
        if (ons === 0) {
            setRequestSubmit(false);
        }

    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        let url = "/auth-api/user/info";
        getData(url)
            .then((data) => {
                if (data.info.allowNewRuns) {
                    setDisabled(false)
                } else {
                    setSysMsg(data.info.message)
                    setDisabled(true)
                    setOpenDialog(true)
                }
            })
            .catch((err) => {
                alert(err)
            })
    }, [props])

    return (
        <div className="animated fadeIn" style={disabled ? { pointerEvents: 'none', opacity: '0.4' } : {}}>
            <ToastContainer />
            <LoaderDialog loading={submitting === true} text="Submitting..." />
            <MessageDialog className='modal-lg modal-warning'
                title="System Message"
                isOpen={openDialog}
                html={true}
                message={'<div><b>' + sysMsg + '</b></div>'}
                handleClickClose={closeMsgModal}
            />
            <span className="edge-workflow-tag pt-3 text-muted edge-text-size-small">Metagenomics | Run Multiple Workflows </span>
            <Row className="justify-content-center">
                <Col xs="12" md="10">
                    <Form onSubmit={e => { e.preventDefault(); }}>
                        <div className="clearfix">
                            <h4 className="pt-3">Run Multiple Workflows</h4>
                            <hr />
                            <Project setParams={setProject} />
                            <br></br>
                            <b>Input Raw Reads</b>
                            <br></br>
                            <Input title={"Input"} full_name={"Input"} name={"Input"} setParams={setInputs} />
                            <br></br>
                            {/* <b>Choose Workflows</b>
                            <p>
                                All of the NMDC Metagenomic workflows are connected in EDGE, so that the output of one
                                workflow can automatically be the input for the next workflow if several metagenomic workflows are selected.
                            </p>
                            <br></br>

                            <ReadsQC full_name={workflowlist["ReadsQC"].name} name={"ReadsQC"} setParams={setWorkflowParams} />
                            <ReadbasedAnalysis full_name={workflowlist["ReadbasedAnalysis"].name} name={"ReadbasedAnalysis"} setParams={setWorkflowParams} />
                            <MetaAssembly full_name={workflowlist["MetaAssembly"].name} name={"MetaAssembly"} setParams={setWorkflowParams} />
                            <VirusPlasmid full_name={workflowlist["virus_plasmid"].name} name={"virus_plasmid"} setParams={setWorkflowParams} onoff={metaAssembly_onoff} />
                            <MetaAnnotation full_name={workflowlist["MetaAnnotation"].name} name={"MetaAnnotation"} setParams={setWorkflowParams} onoff={metaAssembly_onoff} />
                            <MetaMAGs full_name={workflowlist["MetaMAGs"].name} name={"MetaMAGs"} setParams={setWorkflowParams} onoff={metaMAGs_onoff} />

                            <br></br> */}

                        </div>

                        <div className="edge-center">
                            <Button color="primary" onClick={e => onSubmit()} disabled={!requestSubmit}>Submit</Button>{' '}
                            <Button color="outline-primary" onClick={e => window.location.reload(false)} >Reset</Button>
                        </div>
                        <br></br>
                        <br></br>
                    </Form>

                </Col>
            </Row>
        </div >
    );
}

export default Main;