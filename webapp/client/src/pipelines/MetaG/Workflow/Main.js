import React, { useState, useEffect } from 'react';
import {
    Button, Form, Row, Col
} from 'reactstrap';

import { getData, postData, notify } from '../../../common/util';
import { LoaderDialog, MessageDialog } from '../../../common/Dialogs';
import MySelect from '../../../common/MySelect';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { workflowlist, workflowOptions } from './Defaults';
import { Project } from '../../Common/Forms/Project';
import { ReadsQC } from './Forms/ReadsQC';
import { ReadbasedAnalysis } from './Forms/ReadbasedAnalysis';
import { MetaAnnotation } from './Forms/MetaAnnotation';
import { MetaAssembly } from './Forms/MetaAssembly';
import { MetaMAGs } from './Forms/MetaMAGs';

function Main(props) {
    const [openDialog, setOpenDialog] = useState(false);
    const [disabled, setDisabled] = useState(false);
    const [sysMsg, setSysMsg] = useState();
    const [submitting, setSubmitting] = useState(false);
    const [requestSubmit, setRequestSubmit] = useState(false);

    const [projectParams, setProjectParams] = useState();

    const [selectedWorkflows, setSelectedWorkflows] = useState({});
    const [doValidation, setDoValidation] = useState(0);

    const [workflow, setWorkflow] = useState();

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
        if (workflow === 'ReadbasedAnalysis') {
            myWorkflow.enabled_tools = selectedWorkflows[workflow].enabled_tools;
            inputDisplay.input['Analysis Tools'] = selectedWorkflows[workflow].enabled_tools;
            myWorkflow.paired = selectedWorkflows[workflow].paired;
            if (selectedWorkflows[workflow].paired) {
                let reads = [];
                selectedWorkflows[workflow].fastqPaired.forEach((paired, id) => {
                    reads.push(paired.fq1);
                    reads.push(paired.fq2);
                });
                myWorkflow.reads = reads;
                inputDisplay.input['Is single-end'] = false;
                let readsDisplay = [];
                selectedWorkflows[workflow].fastqPairedDisplay.forEach((paired, id) => {
                    readsDisplay.push(paired.fq1);
                    readsDisplay.push(paired.fq2);
                });
                inputDisplay.input.fastqs = readsDisplay;
            } else {
                inputDisplay.input['Is single-end'] = true;
                myWorkflow.reads = selectedWorkflows[workflow].fastqSingle;
                inputDisplay.input.fastqs = selectedWorkflows[workflow].fastqSingleDisplay;
            }

        } else if (workflow === 'MetaAnnotation') {
            myWorkflow.input_fasta = selectedWorkflows[workflow].input_fasta;
            inputDisplay.input['Input FASTA File'] = selectedWorkflows[workflow].input_fasta_display;

        } else if (workflow === 'MetaMAGs') {
            myWorkflow.sam_file= selectedWorkflows[workflow].sam_file;
            myWorkflow.contig_file = selectedWorkflows[workflow].contig_file;
            myWorkflow.proteins_file = selectedWorkflows[workflow].proteins_file;
            myWorkflow.gff_file = selectedWorkflows[workflow].gff_file;
            myWorkflow.cog_file = selectedWorkflows[workflow].cog_file;
            myWorkflow.ec_file = selectedWorkflows[workflow].ec_file;
            myWorkflow.ko_file = selectedWorkflows[workflow].ko_file;
            myWorkflow.pfam_file = selectedWorkflows[workflow].pfam_file;
            myWorkflow.tigrfam_file = selectedWorkflows[workflow].tigrfam_file;
            myWorkflow.crispr_file = selectedWorkflows[workflow].crispr_file;
            myWorkflow.product_names_file = selectedWorkflows[workflow].product_names_file;
            myWorkflow.gene_phylogeny_file = selectedWorkflows[workflow].gene_phylogeny_file;
            myWorkflow.lineage_file = selectedWorkflows[workflow].lineage_file;
            myWorkflow.map_file = selectedWorkflows[workflow].map_file;

            inputDisplay.input['sam/bam file'] = selectedWorkflows[workflow].sam_file_display;
            inputDisplay.input['contig file'] = selectedWorkflows[workflow].contig_file_display;
            inputDisplay.input['proteins file'] = selectedWorkflows[workflow].proteins_file_display;
            inputDisplay.input['gff file'] = selectedWorkflows[workflow].gff_file_display;
            inputDisplay.input['cog file'] = selectedWorkflows[workflow].cog_file_display;
            inputDisplay.input['ec file'] = selectedWorkflows[workflow].ec_file_display;
            inputDisplay.input['ko file'] = selectedWorkflows[workflow].ko_file_display;
            inputDisplay.input['pfam file'] = selectedWorkflows[workflow].pfam_file_display;
            inputDisplay.input['tigrfam file'] = selectedWorkflows[workflow].tigrfam_file_display;
            inputDisplay.input['crispr file'] = selectedWorkflows[workflow].crispr_file_display;
            inputDisplay.input['product_names file'] = selectedWorkflows[workflow].product_names_file_display;
            inputDisplay.input['gene_phylogeny file'] = selectedWorkflows[workflow].gene_phylogeny_file_display;
            inputDisplay.input['lineage file'] = selectedWorkflows[workflow].lineage_file_display;
            inputDisplay.input['map file'] = selectedWorkflows[workflow].map_file_display;

        } else if (workflow === 'MetaAssembly' || workflow === 'ReadsQC') {
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
            <span className="edge-workflow-tag pt-3 text-muted edge-text-size-small">Metagenomics | Run Single Workflow </span>
            <Row className="justify-content-center">
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
                            <h4 className="pt-3">Run a Single Workflow</h4>
                            <hr />
                            <Project setParams={setProject} />

                            <br></br>
                            <b>Workflow</b>
                            <MySelect
                                //defaultValue={workflowOptions[0]}
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
                                    {workflowlist[workflow].info} <a target="_blank" href={workflowlist[workflow].doclink} rel="noopener noreferrer">Learn more</a>
                                    <br></br>
                                </>
                            }
                            <br></br>
                            {workflow === 'ReadsQC' &&
                                <ReadsQC name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                            }
                            {workflow === 'ReadbasedAnalysis' &&
                                <ReadbasedAnalysis name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                            }
                            {workflow === 'MetaAssembly' &&
                                <MetaAssembly name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                            }
                            {workflow === 'MetaAnnotation' &&
                                <MetaAnnotation name={workflow} full_name={workflow} setParams={setWorkflowParams} />
                            }
                            {workflow === 'MetaMAGs' &&
                                <MetaMAGs name={workflow} full_name={workflow} setParams={setWorkflowParams} />
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