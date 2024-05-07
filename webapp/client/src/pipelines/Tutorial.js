import React from 'react';
import { Col, Row } from 'reactstrap';
import { intro, pipelinelist, workflowlist } from './Defaults';
import TutorialBar from './Common/TutorialBar';
import TutorialBarDropdown from './Common/TutorialBarDropdown';

import spainFlag from '../assets/img/spain-flag.png';
import franceFlag from '../assets/img/france-flag.png';


function Tutorial() {
    return (
        <div className="animated fadeIn">
            <br></br>
            <Row className="justify-content-center" >
                <Col xs="12" md="10">
                    <Row style={{ fontWeight: 'bold', fontSize: '16px' }}>
                        <Col xs="3" md="3" lg="2"></Col>
                        <Col xs="2" md="2" lg="2"><center>Tutorial Videos</center></Col>
                        <Col xs="2" md="2" lg="2"><center>User Guides</center></Col>
                        <Col xs="2" md="2" lg="2"><center>Guías de Usuario <img alt="" style={{ width: 15, height: 15 }} src={spainFlag} /></center></Col>
                        <Col xs="2" md="2" lg="2"><center>Guides d'Utilisation <img alt="" style={{ width: 15, height: 15 }} src={franceFlag} /></center></Col>
                        <Col xs="3" md="3" lg="2"><center>Command Line & Additional Documentation</center></Col>
                    </Row>
                    <br></br>
                    <TutorialBar
                        title={intro.title}
                        name={intro.name}
                        docs={intro.doclink ? intro.doclink : null}
                        pdf={intro.pdf ? intro.pdf : null}
                        pdfSpanish={intro.pdfSpanish ? intro.pdfSpanish : null}
                        pdfFrench={intro.pdfFrench ? intro.pdfFrench : null}
                        video={intro.video ? intro.video : null}
                        bgcolor={intro.bgcolor}
                    />
                    <br></br>
                    {Object.keys(pipelinelist).map((item, index) => {
                        return (
                            <div key={index}>
                                <TutorialBarDropdown key={index}
                                    title={pipelinelist[item].title}
                                    name={pipelinelist[item].name}
                                    docs={pipelinelist[item].doclink ? pipelinelist[item].doclink : null}
                                    pdf={pipelinelist[item].pdf ? pipelinelist[item].pdf : null}
                                    pdfSpanish={pipelinelist[item].pdfSpanish ? pipelinelist[item].pdfSpanish : null}
                                    pdfFrench={pipelinelist[item].pdfFrench ? pipelinelist[item].pdfFrench : null}
                                    video={pipelinelist[item].video ? pipelinelist[item].video : null}
                                    bgcolor={pipelinelist[item].bgcolor}
                                />
                                <br></br>
                            </div>
                        )
                    })}
                    {Object.keys(workflowlist).map((item, index) => {
                        return (
                            <div key={index}>
                                <TutorialBar key={index}
                                    title={workflowlist[item].title}
                                    name={workflowlist[item].name}
                                    docs={workflowlist[item].doclink ? workflowlist[item].doclink : null}
                                    pdf={workflowlist[item].pdf ? workflowlist[item].pdf : null}
                                    pdfSpanish={workflowlist[item].pdfSpanish ? workflowlist[item].pdfSpanish : null}
                                    pdfFrench={workflowlist[item].pdfFrench ? workflowlist[item].pdfFrench : null}
                                    video={workflowlist[item].video ? workflowlist[item].video : null}
                                    bgcolor={workflowlist[item].bgcolor}
                                />
                                <br></br>
                            </div>
                        )
                    })}
                </Col>
            </Row>
        </div>

    );
}

export default Tutorial;
