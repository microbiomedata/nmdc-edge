import React, { useState } from 'react';
import {
  Col, Row, Button
} from 'reactstrap';
import { FileViewerDialog } from '../../common/Dialogs';
import { fetchFile } from '../../common/util';
import BulkSubmissionProjects from './Results/BulkSubmissionProjects';

function BulkSubmissionResult(props) {
  const [view_log_file, setView_log_file] = useState(false);
  const [log_file_content, setLog_file_content] = useState('');

  function viewLogFile() {
    let url = "/bulkSubmissions/" + props.bulkSubmission.code + "/log.txt";
    fetchFile(url)
      .then(data => {
        setLog_file_content(data);
        setView_log_file(true);
      })
      .catch((error) => {
        alert(error);
      });;
  }

  function onLogChange(data) {
    setLog_file_content(data);
  }

  return (
    <div className="animated fadeIn">
      <FileViewerDialog type={'text'} isOpen={view_log_file} toggle={e => setView_log_file(!view_log_file)} title={'log.txt'}
        src={log_file_content} onChange={onLogChange} />

      {(props.bulkSubmission && props.bulkSubmission.status === 'failed' && props.type !== 'public') &&
        <>
          <Row className="justify-content-center">
            <Col xs="12" md="10">
              <Button type="button" size="sm" color="primary" onClick={viewLogFile} >View Log</Button>
            </Col>
          </Row>
          <br></br>
        </>
      }
      <br></br>
      {props.bulkSubmission && props.bulkSubmission.status === 'complete' &&
        <Row className="justify-content-center">
          <Col xs="12" md="10">
            <BulkSubmissionProjects tableType={props.type} title={"Projects"} code={props.bulkSubmission.code} {...props} />
          </Col>
        </Row>
      }
      <br></br>
      <br></br>
    </div >
  );
}

export default BulkSubmissionResult;