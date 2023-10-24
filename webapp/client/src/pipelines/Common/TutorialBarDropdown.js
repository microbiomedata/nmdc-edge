import React, { useState } from 'react';
import { Col, Row } from 'reactstrap';
import { SiReadthedocs } from 'react-icons/si';
import { GrDocumentPdf } from 'react-icons/gr';
import { FaFilePdf } from 'react-icons/fa';
import { FiVideo } from 'react-icons/fi';
import {
    CDropdown,
    CDropdownMenu,
    CDropdownToggle,
} from '@coreui/react';

import { VideoDialog } from '../../common/Dialogs';
import TutorialBarDropdownItem from './TutorialBarDropdownItem';
import TutorialBarDropdownVideoItem from './TutorialBarDropdownVideoItem';

function TutorialBarDropdown(props) {
    const [video, setVideo] = useState();
    const [name, setName] = useState();
    const [openVideo, setOpenVideo] = useState(false);

    const closeVideo = () => {
        setOpenVideo(false);
    }
    const toggleVideo = () => setOpenVideo(!openVideo);

    const setItem = (name, video) => {
        setName(name);
        setVideo(process.env.REACT_APP_API_URL + video);
        setOpenVideo(true);
    }

    return (
        <>
            <VideoDialog title={name} isOpen={openVideo} video={video} toggle={toggleVideo}
                handleClickClose={closeVideo} />

            <Row style={{
                display: "flex", justifyContent: "center", alignItems: "center", color: 'white', fontWeight: 'bold', fontSize: '20px',
                backgroundColor: props.bgcolor, height: '60px'
            }}>
                <Col xs="3" md="3" lg="3">{props.title}</Col>
                <Col xs="2" md="2" lg="2">
                    {props.video &&
                        <center>
                            <CDropdown direction="down" >
                                <CDropdownToggle style={{ color: 'white' }} caret={true} className="no-outline">
                                    <FiVideo fontSize="large" />
                                </CDropdownToggle>
                                <CDropdownMenu className="pt-0" placement="bottom">
                                    <div style={{
                                        display: "flex", justifyContent: "center", alignItems: "center", color: 'white',
                                        backgroundColor: 'black', fontWeight: 'bold', height: '30px'
                                    }}>Workflows</div>
                                    <TutorialBarDropdownVideoItem items={props.video} setItem={setItem} />
                                </CDropdownMenu>
                            </CDropdown>
                        </center>
                    }
                </Col>
                <Col xs="2" md="2" lg="2">
                    {props.pdf &&
                        <center>
                            <CDropdown direction="down" >
                                <CDropdownToggle style={{ color: 'white' }} caret={true} className="no-outline">
                                    <FaFilePdf fontSize="large" />
                                </CDropdownToggle>
                                <CDropdownMenu className="pt-0" placement="bottom">
                                    <div style={{
                                        display: "flex", justifyContent: "center", alignItems: "center", color: 'white',
                                        backgroundColor: 'black', fontWeight: 'bold', height: '30px'
                                    }}>Workflows</div>
                                    <TutorialBarDropdownItem items={props.pdf} url={process.env.REACT_APP_API_URL} />
                                </CDropdownMenu>
                            </CDropdown>
                        </center>
                    }
                </Col>
                <Col xs="2" md="2" lg="2">
                    {props.pdfSpanish &&
                        <center>
                            <CDropdown direction="down" >
                                <CDropdownToggle style={{ color: 'white' }} caret={true} className="no-outline">
                                    <FaFilePdf fontSize="large" />
                                </CDropdownToggle>
                                <CDropdownMenu className="pt-0" placement="bottom">
                                    <div style={{
                                        display: "flex", justifyContent: "center", alignItems: "center", color: 'white',
                                        backgroundColor: 'black', fontWeight: 'bold', height: '30px'
                                    }}>Workflows</div>
                                    <TutorialBarDropdownItem items={props.pdfSpanish} url={process.env.REACT_APP_API_URL} />
                                </CDropdownMenu>
                            </CDropdown>
                        </center>
                    }
                </Col>
                <Col xs="3" md="3" lg="3">
                    {props.docs &&
                        <center>
                            <CDropdown direction="down" >
                                <CDropdownToggle style={{ color: 'white' }} caret={true} className="no-outline">
                                    <SiReadthedocs fontSize="large" style={{ color: 'white' }} />
                                </CDropdownToggle>
                                <CDropdownMenu className="pt-0" placement="bottom">
                                    <div style={{
                                        display: "flex", justifyContent: "center", alignItems: "center", color: 'white',
                                        backgroundColor: 'black', fontWeight: 'bold', height: '30px'
                                    }}>Workflows</div>
                                    <TutorialBarDropdownItem items={props.docs} url={''} />
                                </CDropdownMenu>
                            </CDropdown>
                        </center>
                    }

                </Col>
            </Row>
        </>
    );
}

export default TutorialBarDropdown;