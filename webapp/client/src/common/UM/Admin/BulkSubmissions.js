import React from 'react';
import { Col, Row, } from 'reactstrap';
import BulkSubmissionTable from '../Common/BulkSubmissionTable';

function BulkSubmissions(props) {
    return (
        <div className="animated fadeIn">
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <BulkSubmissionTable tableType='admin' title={"Manage Submissions"} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default BulkSubmissions;