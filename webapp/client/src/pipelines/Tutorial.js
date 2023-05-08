import React from 'react';
import { Col, Row } from 'reactstrap';
import { intro, pipelinelist } from './Defaults';
import TutorialBar from './Common/TutorialBar';
import TutorialBarDropdown from './Common/TutorialBarDropdown';


function Tutorial() {
    return (
        <div className="animated fadeIn">
            <br></br>
            <Row className="justify-content-center" >
                <Col xs="12" md="10">
                    <Row style={{ fontWeight: 'bold', fontSize: '16px' }}>
                        <Col xs="3" md="3" lg="3"></Col>
                        <Col xs="3" md="3" lg="3"><center>The basics</center></Col>
                        <Col xs="3" md="3" lg="3"><center>User Guides</center></Col>
                        <Col xs="3" md="3" lg="3"><center>CLI Information</center></Col>
                    </Row>
                    <br></br>
                    <TutorialBar
                        title={intro.title}
                        name={intro.name}
                        docs={intro.doclink ? intro.doclink : null}
                        pdf={intro.pdf ? intro.pdf : null}
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
                                    video={pipelinelist[item].video ? pipelinelist[item].video : null}
                                    bgcolor={pipelinelist[item].bgcolor}
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
