import React, { useState } from 'react';
import { Col, Row } from 'reactstrap';
import IconButton from '@material-ui/core/IconButton';
import { SiReadthedocs } from 'react-icons/si';
import { GrDocumentPdf } from 'react-icons/gr';
import { FaFilePdf } from 'react-icons/fa';
import { FiVideo } from 'react-icons/fi';

import { VideoDialog } from '../../common/Dialogs';

function TutorialBar(props) {
    const [video, setVideo] = useState();
    const [name, setName] = useState();
    const [openVideo, setOpenVideo] = useState(false);

    const closeVideo = () => {
        setOpenVideo(false);
    }
    const toggleVideo = () => setOpenVideo(!openVideo);

    return (
        <>
            <VideoDialog title={props.name} isOpen={openVideo} video={props.video} toggle={toggleVideo}
                handleClickClose={closeVideo} />

            <Row style={{
                display: "flex", justifyContent: "center", alignItems: "center", color: 'white', fontWeight: 'bold', fontSize: '20px',
                backgroundColor: props.bgcolor, height: '60px'
            }}>
                <Col xs="3" md="3" lg="3">{props.title}</Col>
                <Col xs="3" md="3" lg="3">
                    {props.video &&
                        <center>
                            <IconButton style={{ color: 'white' }} aria-label="video tutorial" onClick={() => { setOpenVideo(true) }}>
                                <FiVideo />
                            </IconButton>
                        </center>
                    }
                </Col>
                <Col xs="3" md="3" lg="3">
                    {props.pdf &&
                        <center>
                            <IconButton style={{ color: 'white' }} aria-label="pdf" href={process.env.REACT_APP_API_URL + props.pdf} target="_blank">
                                <FaFilePdf />
                            </IconButton>
                        </center>
                    }
                </Col>
                <Col xs="3" md="3" lg="3">
                    {props.docs &&
                        <center>
                            <IconButton aria-label="docs" href={process.env.REACT_APP_API_URL + props.docs} target="_blank">
                                <SiReadthedocs style={{ backgroundColor: 'white' }} />
                            </IconButton>
                        </center>
                    }
                </Col>
            </Row>
        </>
    );
}

export default TutorialBar;