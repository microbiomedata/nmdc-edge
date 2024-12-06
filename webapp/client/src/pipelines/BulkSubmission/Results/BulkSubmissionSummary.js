import React from 'react';
import { Col, Row, Badge } from 'reactstrap';
import Moment from 'react-moment';
import { useSelector } from 'react-redux';

import { bulkSubmissionStatusColors, bulkSubmissionStatusNames } from '../../../common/table';

function BulkSubmissionSummary(props) {
  const user = useSelector(state => state.user);

  return (
    <>
      {!props.bulkSubmission ?
        <Row className="justify-content-center">
          <Col xs="12" md="10">
            <div className="clearfix">
              <h4 className="pt-3">BulkSubmission not found</h4>
              <hr />
              <p className="text-muted float-left">
                The bulkSubmission might be deleted or you have no permission to access it.
              </p>
            </div>
          </Col>
        </Row>
        :
        <Row className="justify-content-center">
          <Col xs="12" md="10">
            <div className="clearfix">
              <h4 className="pt-3">{props.bulkSubmission.name}</h4>
              <hr />
              <b>BulkSubmission Summary:</b>
              <hr></hr>
              <b>Description:</b> {props.bulkSubmission.desc}<br></br>
              {props.type !== 'public' && <><b>Owner:</b> {props.bulkSubmission.owner}<br></br></>}
              <b>Submission Time:</b> <Moment>{props.bulkSubmission.created}</Moment><br></br>
              <b>Status:</b> <Badge color={bulkSubmissionStatusColors[props.bulkSubmission.status]}>{bulkSubmissionStatusNames[props.bulkSubmission.status]}</Badge>
              <br></br>
              {props.bulkSubmission.status === 'failed' && <span className='edge-help-text'>
                {props.type === 'user' && props.bulkSubmission.owner === user.profile.email && <>
                  If you need assistance with this failed bulkSubmission, please contact nmdc-edge@lanl.gov and include the bulkSubmission code '{props.bulkSubmission.code}'.
                  <br></br>
                </>}
              </span>}
              <b>Type:</b> {props.bulkSubmission.type}<br></br>
              <b>File:</b> {props.bulkSubmission.filename}<br></br>
            </div>
          </Col>
        </Row>
      }
    </>
  );
}

export default BulkSubmissionSummary;