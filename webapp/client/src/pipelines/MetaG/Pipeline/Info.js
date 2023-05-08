import React, { Component } from 'react';
import { Col, Row } from 'reactstrap';
import workflowImg from '../../assets/img/workflows.png';

class Info extends Component {
    render() {
        return (
            <div className="animated fadeIn">
                <span className="pt-3 text-muted edge-text-size-small">Metagenome | Information</span>
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">Information</h4>

                            <p className="edge-text-font float-left">
                                This is a pipeline of NMDC Metagenomic workflows. All workflows are connected in EDGE, so that the output of one workflow can
                                automatically be the input for the next workflow if several metagenomic workflows are selected.
                            </p>
                        </div>
                    </Col>
                </Row>
                <br></br>
                <Row className="justify-content-center">
                    <Col xs="12" md="8">
                        <img alt={""} src={workflowImg} width={'100%'} height={'100%'}/>
                    </Col>
                </Row>
                <br></br>
            </div>
        );
    }
}

export default Info;
