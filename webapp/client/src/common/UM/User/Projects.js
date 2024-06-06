import React from 'react';
import { Col, Row, } from 'reactstrap';
import ProjectTable from '../Common/ProjectTable';

function Projects(props) {
    return (
        <div className="animated fadeIn">
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