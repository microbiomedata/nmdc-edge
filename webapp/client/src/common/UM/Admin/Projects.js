import React from 'react';
import { Badge, Col, Row } from 'reactstrap';
import ProjectTable from '../Common/ProjectTable';

function Projects(props) {
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
                    <ProjectTable tableType='admin' title={"Manage Projects"} {...props}/>
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Projects;