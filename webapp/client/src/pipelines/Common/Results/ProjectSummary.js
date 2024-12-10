import React from 'react';
import { Col, Row, Badge } from 'reactstrap';
import Moment from 'react-moment';
import { useSelector } from 'react-redux';

import { projectStatusColors, projectStatusNames } from '../../../common/table';

function ProjectSummary(props) {
    const user = useSelector(state => state.user);

    return (
        <>
            {!props.project ?
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">Project not found</h4>
                            <hr />
                            <p className="text-muted float-left">
                                The project might be deleted or you have no permission to access it.
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
                            <b>Status:</b> <Badge color={projectStatusColors[props.project.status]}>{projectStatusNames[props.project.status]}</Badge>
                            <br></br>
                            {props.project.status === 'failed' && <span className='edge-help-text'>
                                {props.type === 'user' && props.project.owner === user.profile.email && <>
                                    If you need assistance with this failed project, please contact nmdc-edge@lanl.gov and include the project code '{props.project.code}'.
                                    <br></br>
                                </>}
                            </span>}
                            <b>Type:</b> {props.project.type}<br></br>
                        </div>
                    </Col>
                </Row>
            }
        </>
    );
}

export default ProjectSummary;