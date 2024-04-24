import React from 'react';
import { Col, Row, Badge } from 'reactstrap';
import Moment from 'react-moment';

import { projectStatusColors, projectStatusNames } from '../../../common/table';

function ProjectSummary(props) {
    return (
        <>
            {!props.project ?
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">Project not found</h4>
                            <hr />
                            <p className="text-muted float-left">
                                The project might be deleted or you have no permission to acces it.
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">{props.project.name}</h4>
                            <hr />
                            <b>Project Summary:</b>
                            <hr></hr>
                            <b>Description:</b> {props.project.desc}<br></br>
                            {props.type !== 'public' && <><b>Owner:</b> {props.project.owner}<br></br></>}
                            <b>Submission Time:</b> <Moment>{props.project.created}</Moment><br></br>
                            <b>Status:</b> <Badge color={projectStatusColors[props.project.status]}>{projectStatusNames[props.project.status]}</Badge><br></br>
                            <b>Type:</b> {props.project.type}<br></br>
                        </div>
                    </Col>
                </Row>
            }
        </>
    );
}

export default ProjectSummary;