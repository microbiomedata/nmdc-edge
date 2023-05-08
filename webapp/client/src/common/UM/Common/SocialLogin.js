import React, { useState } from 'react';
import { Col, Row } from 'reactstrap';

import { useDispatch, useSelector } from 'react-redux';
import GoogleLogin from "react-google-login";
import FacebookLogin from 'react-facebook-login/dist/facebook-login-render-props';
import {
    FacebookLoginButton,
    GoogleLoginButton
} from "react-social-login-buttons";
import ORCIDLoginButton from './ORCIDLoginButton';
import { popupWindow } from '../../util';

import { socialLogin, cleanupMessages } from "../../../redux/actions/userActions";
import { LoaderDialog, ConfirmDialogNoHeader, MessageDialog } from '../../Dialogs';

export function SocialLogin(props) {
    const dispatch = useDispatch();
    const errors = useSelector(state => state.errors);
    const messages = useSelector(state => state.messages);
    const page = useSelector(state => state.page);

    const [userData, setUserData] = useState({});
    const [openConfirm, setOpenConfirm] = useState(false);

    const closeConfirm = () => {
        setOpenConfirm(false);
    }
    const handleYes = () => {
        setOpenConfirm(false);

        //clean up error messages
        dispatch(cleanupMessages());
        //social login
        var status = "active";
        if (process.env.REACT_APP_EMAIL_NOTIFICATION === 'true') {
            status = "inactive";
        }
        if (userData.socialtype === 'orcid') {
            status = "active";
            if (!userData.lastname) {
                //is optional in ORCiD
                userData.lastname = 'unknown';
            }
        }
        userData.status = status;

        dispatch(socialLogin(userData));
    }

    const responseGoogle = (response) => {
        //console.log(response);
        const profile = response.profileObj;
        if (profile) {
            const user = {
                firstname: profile.givenName,
                lastname: profile.familyName,
                email: profile.email,
                socialtype: 'google',
                password: profile.googleId + process.env.REACT_APP_SOCIAL_SECRET
            };

            setUserData(user);
            setOpenConfirm(true);
        }
    }

    const responseFacebook = (response) => {
        //console.log(response);
        const name = response.name;
        if (name) {
            let parts = name.split(/\s+/);
            const lastName = parts.pop();
            const firstName = parts.join(' ');

            const user = {
                firstname: firstName,
                lastname: lastName,
                email: response.email,
                socialtype: 'facebook',
                password: response.userID + process.env.REACT_APP_SOCIAL_SECRET
            };

            setUserData(user);
            setOpenConfirm(true);
        }
    }

    const getORCID = () => {
        //ORICD config
        const url = process.env.REACT_APP_ORCID_AUTH_URL;
        console.log(url)
        //open ORCiD login page
        popupWindow(url, 'ORCiD', window, 600, 700);
        // Add a message listener to handle popup messages
        window.addEventListener('message', HandleMessages);
    }
    const HandleMessages = (message) => {
        // Remove message listener after message was received
        window.removeEventListener('message', HandleMessages)

        // Do stuff
        //console.log("got mes", message)
        const data = message.data;
        const user = {
            firstname: data.given_name,
            lastname: data.family_name,
            email: data.sub + "@orcid.org",
            socialtype: 'orcid',
            password: data.sub + process.env.REACT_APP_SOCIAL_SECRET
        };

        setUserData(user);
        setOpenConfirm(true);
    }

    const closeMsgModal = () => {
        //clean up error messages
        dispatch(cleanupMessages());
    }

    return (
        <>
            <LoaderDialog loading={page.submitting_form} text="Verifying email..." />
            <ConfirmDialogNoHeader html={true} isOpen={openConfirm} action={"Continue to " + process.env.REACT_APP_NAME + "?"}
                message={"Hi " + userData.firstname + ",<br/><br/> Welcome to " + process.env.REACT_APP_NAME + "!<br/>"}
                handleClickClose={closeConfirm} handleClickYes={handleYes} />
            <MessageDialog isOpen={messages.sociallogin ? true : false} message={messages.sociallogin} handleClickClose={closeMsgModal} />
            <MessageDialog isOpen={errors.sociallogin ? true : false} message={errors.sociallogin} handleClickClose={closeMsgModal} className='modal-danger' />
            <p className="text-muted">Use a social account for faster login or registration</p>
            {process.env.REACT_APP_GOOGLE_AUTH === 'on' &&
                <Row className="justify-content-center">
                    <Col md="10">
                        <GoogleLogin
                            clientId={process.env.REACT_APP_GOOGLE_ID}
                            onSuccess={responseGoogle}
                            onFailure={(responseGoogle)}
                            cookiePolicy={'single_host_origin'}
                            render={renderProps => (
                                <GoogleLoginButton align='center' size="40px" iconSize="20px" onClick={renderProps.onClick}
                                    disabled={renderProps.disabled} >Login with Google</GoogleLoginButton>
                            )}
                            prompt="select_account"
                        />
                    </Col>
                </Row>
            }
            {process.env.REACT_APP_FACEBOOK_AUTH === 'on' &&
                <Row className="justify-content-center">
                    <Col md="10">
                        <FacebookLogin
                            appId={process.env.REACT_APP_FACEBOOK_ID}
                            fields="name,email"
                            callback={responseFacebook}
                            render={renderProps => (
                                <FacebookLoginButton align='center' size="40px" iconSize="20px" onClick={renderProps.onClick} >Login with Facebook</FacebookLoginButton>
                            )}
                            autoLoad={false}
                            cookie={false}
                        />
                    </Col>
                </Row>
            }
            {process.env.REACT_APP_ORCID_AUTH === 'on' &&
                <Row className="justify-content-center">
                    <Col md="10">
                        <ORCIDLoginButton align='center' size="40px" onClick={e => getORCID()} />
                    </Col>
                </Row>
            }
        </>
    );
}