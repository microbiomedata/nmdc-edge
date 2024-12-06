import React from 'react';
import { Col, Row, } from 'reactstrap';
import {
    CHeaderNavLink,
} from '@coreui/react';
import ProjectTable from '../Common/ProjectTable';

function Projects(props) {
    return (
        <div className="animated fadeIn">
        <Row className="edge-right">
            <Col xl={1}></Col>
            <Col xl={10}>
                <CHeaderNavLink className="btn btn-pill btn-sm btn-outline-primary" to="/user/allprojectlist">Show all projects available to me</CHeaderNavLink>
            </Col>
        </Row>
        <br></br>
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <ProjectTable tableType='user' title={"My Projects"} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Projects;