import React, { useState, useEffect } from 'react';
import {
    Button, Form, Row, Col, Card, CardBody
} from 'reactstrap';

import { getData, postData, notify } from '../../../common/util';
import { LoaderDialog, MessageDialog } from '../../../common/Dialogs';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { workflowlist, workflowOptions } from './Defaults';
import SraDataTable from '../../../common/UM/Common/SraDataTable';
import { Sra2fastq } from './Forms/Sra2fastq';
const HtmlToReactParser = require('html-to-react').Parser;
let htmlToReactParser = new HtmlToReactParser();

function Main(props) {
    const [openDialog, setOpenDialog] = useState(false);
    const [disabled, setDisabled] = useState(false);
    const [sysMsg, setSysMsg] = useState();
    const [submitting, setSubmitting] = useState(false);
    const [requestSubmit, setRequestSubmit] = useState(false);

    const [projectParams] = useState();

    const [selectedWorkflows, setSelectedWorkflows] = useState({});
    const [doValidation, setDoValidation] = useState(0);

    const [workflow] = useState(workflowOptions[0].value);
    const [refreshTable, setRefreshTable] = useState(0)

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
        formData.append('project', JSON.stringify({ name: selectedWorkflows[workflow].accessions, desc: selectedWorkflows[workflow].accessions }));

        let inputDisplay = {};
        inputDisplay.workflow = workflowlist[workflow].title;
        inputDisplay.input = {};
        let myWorkflow = {};
        myWorkflow.name = workflow;
        if (workflow === 'sra2fastq') {
            myWorkflow['accessions'] = selectedWorkflows[workflow].accessions;
            inputDisplay.input['SRA Accession(s)'] = selectedWorkflows[workflow].accessions;
        }

        formData.append('workflow', JSON.stringify(myWorkflow));
        formData.append('inputDisplay', JSON.stringify(inputDisplay));

        postData("/auth-api/user/project/add", formData)
            .then(data => {
                notify("success", "Your workflow request was submitted successfully!", 2000);
                setRefreshTable(refreshTable + 1);
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
    }, [props]);

    return (
        <div className="animated fadeIn">
            <Row className="justify-content-center" style={disabled ? { pointerEvents: 'none', opacity: '0.4' } : {}}>
                <Col xs="12" md="10">
                    <ToastContainer />
                    <LoaderDialog loading={submitting === true} text="Submitting..." />
                    <MessageDialog className='modal-lg modal-warning'
                        title="System Message"
                        isOpen={openDialog}
                        html={true}
                        message={'<div><b>' + sysMsg + '</b></div>'}
                        handleClickClose={closeMsgModal}
                    />
                    <Form onSubmit={e => { e.preventDefault(); }}>
                        <div className="clearfix">
                            <h4 className="pt-3">Retrieve SRA Data</h4>
                            {workflow &&
                                <>
                                    {htmlToReactParser.parse(workflowlist[workflow].info)} 
                                    {/* <a target="_blank" href={workflowlist[workflow].link} rel="noopener noreferrer">Learn more</a> */}
                                    <br></br>
                                </>
                            }
                        </div>
                        <br></br>
                        <Card className="workflow-card">
                            <CardBody>
                                {workflow === 'sra2fastq' &&
                                    <Sra2fastq reset={refreshTable} name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                                }
                                <br></br>

                                <div className="edge-center">
                                    <Button color="primary" onClick={e => onSubmit()} disabled={!workflow || !requestSubmit}>Submit</Button>{' '}
                                </div>
                            </CardBody>
                        </Card >
                        <br></br>
                        <br></br>
                    </Form>
                </Col>
            </Row>
            <Row>
                <Col xl={1}>
                </Col>
                <Col xl={10}>
                    <SraDataTable tableType='user' title={"My SRA Data"} refresh={refreshTable} {...props} />
                </Col>
            </Row>
            <br></br>
        </div >
    );
}

export default Main;