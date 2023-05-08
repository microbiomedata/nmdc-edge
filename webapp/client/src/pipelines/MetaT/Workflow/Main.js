import React, { useState, useEffect } from 'react';
import {
    Button, Form, Row, Col
} from 'reactstrap';

import { postData, notify } from '../../../common/util';
import { LoaderDialog, MessageDialog } from '../../../common/Dialogs';
import MySelect from '../../../common/MySelect';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { workflowlist, workflowOptions } from './Defaults';
import { Project } from '../../Common/Forms/Project';
import { Metatranscriptome } from './Forms/Metatranscriptome';

function Main(props) {
    const [openDialog, setOpenDialog] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [requestSubmit, setRequestSubmit] = useState(false);

    const [projectParams, setProjectParams] = useState();

    const [selectedWorkflows, setSelectedWorkflows] = useState({});
    const [doValidation, setDoValidation] = useState(0);

    const [workflow, setWorkflow] = useState(workflowOptions[0].value);

    //callback function for child component
    const setProject = (params) => {
        //console.log("main project:", params)
        setProjectParams(params);
        setDoValidation(doValidation + 1);
    }
    const setWorkflowParams = (params, workflowName) => {
        //console.log("workflow:", params, workflowName)
        setSelectedWorkflows({ ...selectedWorkflows, [workflowName]: params });
        setDoValidation(doValidation + 1);
    }

    const closeMsgModal = () => {
        setOpenDialog(false);
    }
    //submit button clicked
    const onSubmit = () => {

        let formData = new FormData();

        formData.append('pipeline', workflowlist[workflow].title);
        formData.append('project', JSON.stringify({ name: projectParams.proj_name, desc: projectParams.proj_desc }));

        let inputDisplay = {};
        inputDisplay.workflow = workflowlist[workflow].title;
        inputDisplay.input = {};
        let myWorkflow = {};
        myWorkflow.name = workflow;
        if (workflow === 'Metatranscriptome') {
            let myInputs = {};
            if (selectedWorkflows[workflow].interleaved) {
                myInputs.interleaved = true;
                myInputs.fastqs = selectedWorkflows[workflow].fastqSingle;
                inputDisplay.input['Is interleaved'] = true;
                inputDisplay.input.fastqs = selectedWorkflows[workflow].fastqSingleDisplay;
            } else {
                myInputs.interleaved = false;
                myInputs.fastqs = selectedWorkflows[workflow].fastqPaired;
                inputDisplay.input['Is interleaved'] = false;
                inputDisplay.input.fastqs = selectedWorkflows[workflow].fastqPairedDisplay;
            }
            myWorkflow.input_fastq = myInputs;
        } 

        formData.append('workflow', JSON.stringify(myWorkflow));
        formData.append('inputDisplay', JSON.stringify(inputDisplay));

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
        setRequestSubmit(true);

        if (projectParams && !projectParams.validForm) {
            setRequestSubmit(false);
        }

        if (!workflow || !selectedWorkflows[workflow] || (selectedWorkflows[workflow] && !selectedWorkflows[workflow].validForm)) {
            setRequestSubmit(false);
        }

    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        setDoValidation(doValidation + 1);
    }, [workflow]);// eslint-disable-line react-hooks/exhaustive-deps


    return (

        <div className="animated fadeIn">
            <span className="pt-3 text-muted edge-text-size-small">Metatranscriptomics | Run Single Workflow </span>
            <Row className="justify-content-center">
                <Col xs="12" md="10">
                    <ToastContainer />
                    <LoaderDialog loading={submitting === true} text="Submitting..." />
                    <MessageDialog className='modal-lg modal-danger' title='Failed to submit the form' isOpen={openDialog} html={true}
                        message={"<div><b>Please correct the error(s) and try again.</b></div>"}
                        handleClickClose={closeMsgModal} />
                    <Form onSubmit={e => { e.preventDefault(); }}>
                        <div className="clearfix">
                            <h4 className="pt-3">Run a Single Workflow</h4>
                            <hr />
                            <Project setParams={setProject} />

                            <br></br>
                            <b>Workflow</b>
                            <MySelect
                                value={workflowOptions[0]}
                                options={workflowOptions}
                                onChange={e => {
                                    if (e) {
                                        setWorkflow(e.value);
                                    } else {
                                        setWorkflow();
                                    }
                                }}
                                placeholder="Select a Workflow..."
                                isClearable={true}
                            />
                            <br></br>
                            {workflow &&
                                <>
                                    {workflowlist[workflow].info} <a target="_blank" href={workflowlist[workflow].link} rel="noopener noreferrer">Learn more</a>
                                    <br></br>
                                </>
                            }
                            <br></br>
                            {workflow === 'Metatranscriptome' &&
                                <Metatranscriptome name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                            }
                            <br></br>
                        </div>

                        <div className="edge-center">
                            <Button color="primary" onClick={e => onSubmit()} disabled={!workflow || !requestSubmit}>Submit</Button>{' '}
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