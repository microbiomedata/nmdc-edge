import React, { useState } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardActionArea from '@material-ui/core/CardActionArea';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardMedia from '@material-ui/core/CardMedia';
import Typography from '@material-ui/core/Typography';

import VideocamIcon from '@material-ui/icons/Videocam';
import GitHubIcon from '@material-ui/icons/GitHub';
import IconButton from '@material-ui/core/IconButton';   
import Tooltip from '@material-ui/core/Tooltip';    
import { AiFillGitlab } from 'react-icons/ai';
import { SiReadthedocs } from 'react-icons/si';
import { GrDocumentPdf } from 'react-icons/gr';

import { ImgDialog, VideoDialog } from './Dialogs';
import { colors } from './Colors';

const useStyles = makeStyles({
    Card: {
        maxWidth: 300,
        overflow: "visible",
        borderRadius: "8px",
        display: "grid",
        backgroundColor: colors.light,
    },
    Media: {
        height: 80,
        width: '100%',
        borderTopRightRadius: "8px",
        borderTopLeftRadius: "8px",
        objectFit: 'cover'
    },

    Body: {
        textAlign: "center"
    },

    Footer: {
        display: "flex",
        justifyContent: 'center'
    }
});

function WorkflowCard(props) {
    const classes = useStyles();
    const [openImg, setOpenImg] = useState(false);
    const [openVideo, setOpenVideo] = useState(false);

    const closeImg = () => {
        setOpenImg(false);
    }
    const toggleImg = () => setOpenImg(!openImg);

    const closeVideo = () => {
        setOpenVideo(false);
    }
    const toggleVideo = () => setOpenVideo(!openVideo);

    return (
        <>
            <ImgDialog title={props.name} isOpen={openImg} img={props.img} toggle={toggleImg} imgHeight={props.imgHeight}
                handleClickClose={closeImg} />
            <VideoDialog title={props.name} isOpen={openVideo} video={props.video} toggle={toggleVideo}
                handleClickClose={closeVideo} />
            <Card className={classes.Card}>
                <CardActionArea onClick={() => setOpenImg(true)}>
                    <CardMedia className={classes.Media}
                        component="img"
                        alt={props.alt}
                        image={props.thumbnail}
                        title={"click to view"}
                    />
                </CardActionArea>
                <CardContent className={classes.Body}>
                    <Typography variant="body2" color="textSecondary" component="p">
                        {props.title}
                    </Typography>
                </CardContent>

                <CardActions disableSpacing className={classes.Footer}>
                    {props.video &&
                        <IconButton aria-label="video tutorial" onClick={() => setOpenVideo(true)}>
                            <VideocamIcon />
                        </IconButton>
                    }
                    {props.pdf &&
                        <IconButton aria-label="pdf" href={props.pdf} target="_blank">
                            <GrDocumentPdf />
                        </IconButton>
                    }
                    {props.github &&
                        <IconButton aria-label="github" href={props.github} target="_blank">
                            <GitHubIcon />
                        </IconButton>
                    }
                    {props.gitlab &&
                        <IconButton aria-label="gitlab" href={props.gitlab} target="_blank">
                            <AiFillGitlab />
                        </IconButton>
                    }
                    {props.docs &&
                    <Tooltip title="Instructions for installation and running the workflow at the command line">    
                        <IconButton aria-label="docs" href={props.docs} target="_blank">
                            <SiReadthedocs />
                        </IconButton>
                        </Tooltip>
                    }
                </CardActions>
            </Card>
        </>
    );
}

export { WorkflowCard }