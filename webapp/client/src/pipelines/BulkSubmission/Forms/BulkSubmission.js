import React, { useState, useEffect } from 'react';
import {
  Button, Form, Row, Col
} from 'reactstrap';

import { getData, postData, notify } from '../../../common/util';
import { LoaderDialog, MessageDialog } from '../../../common/Dialogs';
import MySelect from '../../../common/MySelect';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { workflowlist } from '../../Defaults';
import { Project } from '../../Common/Forms/Project';
import { FileUpload } from '../../Common/Forms/FileUpload';
import config from '../../../config';
const HtmlToReactParser = require('html-to-react').Parser;
let htmlToReactParser = new HtmlToReactParser();

function BulkSubmission(props) {
  const [openDialog, setOpenDialog] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [sysMsg, setSysMsg] = useState();
  const [submitting, setSubmitting] = useState(false);
  const [requestSubmit, setRequestSubmit] = useState(false);
  const [projectParams, setProjectParams] = useState();
  const [uploadParams, setUploadParams] = useState();
  const [doValidation, setDoValidation] = useState(0);

  const [workflow, setWorkflow] = useState(props.workflowOptions[0].value);

  //callback function for child component
  const setProject = (params) => {
    //console.log("main project:", params)
    setProjectParams(params);
    setDoValidation(doValidation + 1);
  }
  //callback function for child component
  const setFileUpload = (params) => {
    //console.log("main fileupload:", params)
    setUploadParams(params);
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
    inputDisplay.type = workflowlist[workflow].title;
    inputDisplay.input = {};
    formData.append('file', uploadParams.file);
    formData.append('bulkfile', JSON.stringify({ name: uploadParams.file.name }));
    inputDisplay.input['Bulk Excel File'] = uploadParams.file.name;

    formData.append('inputDisplay', JSON.stringify(inputDisplay));

    //console.log("formdata", JSON.stringify(workflowParams))
    postData("/auth-api/user/bulkSubmission/add", formData)
      .then(data => {
        notify("success", "Your bulk submission request was submitted successfully!", 2000);
        setTimeout(() => props.history.push("/user/bulkSubmission/list"), 2000);
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
    if (uploadParams && !uploadParams.validForm) {
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
      <span className="edge-workflow-tag pt-3 text-muted edge-text-size-small">{props.category} | Bulk Submission</span>
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
              <h4 className="pt-3">Bulk Submission</h4>
              <hr />
              <Project setParams={setProject} text="Name" />
              <br></br>
              <b>Workflow</b>
              {props.workflowOptions.length > 1 ? <>
                <MySelect
                  defaultValue={props.workflowOptions[0]}
                  options={props.workflowOptions}
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
              </> : <><br></br>{props.workflowOptions[0].label}</>}
              <br></br>
              {workflow &&
                <>
                  {workflowlist[workflow] && workflowlist[workflow].info ?
                    <>
                      {workflowlist[workflow].doclink ? <>
                        {htmlToReactParser.parse(workflowlist[workflow].info)} &nbsp;
                        <a target="_blank" href={workflowlist[workflow].doclink} rel="noopener noreferrer">Learn more</a>
                        <br></br><br></br>
                      </>
                        :
                        <>
                          {htmlToReactParser.parse(workflowlist[workflow].info)} &nbsp;
                          <br></br><br></br>
                        </>
                      }
                    </>
                    :
                    <></>
                  }
                  Download Excel <a style={{ color: "blue", textDecoration: "underline" }} rel="noreferrer"
                    href={config.API.BASE_URI + workflowlist[workflow].bulk_submission_template} target="_blank">Template</a>
                  <br></br><br></br>
                  <FileUpload setParams={setFileUpload} text="Bulk Excel File"
                    upload_tip={workflowlist[workflow]['bulk_file_tip'] ? workflowlist[workflow]['bulk_file_tip'] : 'Required'}
                    accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" />
                  <br></br>
                </>
              }
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

export default BulkSubmission;