import React from 'react';
import { Col, Row, } from 'reactstrap';
import FileTable from '../Common/FileTable';

function Files(props) {
    return (
        <div className="animated fadeIn">
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <FileTable tableType='user' title={"Manage Uploads"} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Files;