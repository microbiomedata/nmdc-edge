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
import { VirusPlasmid } from './Forms/VirusPlasmid';
const HtmlToReactParser = require('html-to-react').Parser;
let htmlToReactParser = new HtmlToReactParser();

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
        if (workflow === 'virus_plasmid') {
            // myWorkflow.enabled_modules = selectedWorkflows[workflow].enabled_modules;
            // inputDisplay.input['Analysis Modules'] = selectedWorkflows[workflow].enabled_modules;
            myWorkflow['min_score'] = selectedWorkflows[workflow]['min_score'];
            myWorkflow['min_virus_hallmark'] = selectedWorkflows[workflow]['min_virus_hallmark'];
            myWorkflow['min_plasmid_hallmark'] = selectedWorkflows[workflow]['min_plasmid_hallmark'];
            myWorkflow.input_fasta = selectedWorkflows[workflow].input_fasta;
            myWorkflow.option = selectedWorkflows[workflow].option;
            myWorkflow['min_plasmid_hallmarks_short_seqs'] = selectedWorkflows[workflow]['min_plasmid_hallmarks_short_seqs'];
            myWorkflow['min_virus_hallmarks_short_seqs'] = selectedWorkflows[workflow]['min_virus_hallmarks_short_seqs'];
            myWorkflow['min_plasmid_marker_enrichment'] = selectedWorkflows[workflow]['min_plasmid_marker_enrichment'];
            myWorkflow['min_virus_marker_enrichment'] = selectedWorkflows[workflow]['min_virus_marker_enrichment'];
            myWorkflow['max_uscg'] = selectedWorkflows[workflow]['max_uscg'];
            myWorkflow['score_calibration'] = selectedWorkflows[workflow]['score_calibration'];
            myWorkflow['fdr'] = selectedWorkflows[workflow]['fdr'];

            inputDisplay.input['Input Assembled Fasta File'] = selectedWorkflows[workflow].input_fasta_display;
            inputDisplay.input['Run Option'] = selectedWorkflows[workflow].option;
            inputDisplay.input['Min geNomad Score'] = selectedWorkflows[workflow]['min_score'];
            inputDisplay.input['Min Plasmid Marker Enrichment'] = selectedWorkflows[workflow]['min_plasmid_marker_enrichment'];
            inputDisplay.input['Min Virus Marker Enrichment'] = selectedWorkflows[workflow]['min_virus_marker_enrichment'];
            inputDisplay.input['Min Plasmid Hallmark'] = selectedWorkflows[workflow]['min_plasmid_hallmark'];
            inputDisplay.input['Min Plasmid Hallmarks Short Seqs'] = selectedWorkflows[workflow]['min_plasmid_hallmarks_short_seqs'];
            inputDisplay.input['Min Virus Hallmark'] = selectedWorkflows[workflow]['min_virus_hallmark'];
            inputDisplay.input['Min Virus Hallmarks Short Seqs'] = selectedWorkflows[workflow]['min_virus_hallmarks_short_seqs'];
            inputDisplay.input['Max USCGs'] = selectedWorkflows[workflow]['max_uscg'];
            inputDisplay.input['Score Calibration'] = selectedWorkflows[workflow]['score_calibration'];
            inputDisplay.input['False Discovery Rate'] = selectedWorkflows[workflow]['fdr'];
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
            <span className="pt-3 text-muted edge-text-size-small">Viruses and Plasmids | Run Single Workflow </span>
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
                                //defaultValue={workflowOptions[0]}
                                options={workflowOptions}
                                value={workflowOptions[0]}
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
                                    {htmlToReactParser.parse(workflowlist[workflow].info)} <a target="_blank" href={workflowlist[workflow].link} rel="noopener noreferrer">Learn more</a>
                                    <br></br>
                                </>
                            }
                            <br></br>
                            {workflow === 'virus_plasmid' &&
                                <VirusPlasmid name={workflow} full_name={workflow} setParams={setWorkflowParams} />
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