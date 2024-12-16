import React from 'react';
import { Badge, Col, Row, } from 'reactstrap';
import BulkSubmissionTable from '../Common/BulkSubmissionTable';

function BulkSubmissions(props) {
    return (
        <div className="animated fadeIn">
            <Row >
                <Col xl={1}></Col>
                <Col xl={10}>
                    <div className="clearfix">
                        <Badge href="#" color="danger" pill>Admin tool</Badge>
                    </div>
                </Col>
            </Row>
            <br></br>
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <BulkSubmissionTable tableType='admin' title={"Manage Bulk Submissions"} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default BulkSubmissions;