import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import jwt_decode from "jwt-decode";
import { socialLogin, cleanupMessages } from "../../../redux/actions/userActions";
import { LoaderDialog, MessageDialog } from '../../Dialogs';
import config from "../../../config";

const queryString = require('query-string');

function OrcidLogin(props) {
    const dispatch = useDispatch();
    const errors = useSelector(state => state.errors);
    const messages = useSelector(state => state.messages);
    const page = useSelector(state => state.page);
    const user = useSelector(state => state.user);

    useEffect(() => {
        if (user.isAuthenticated) {
            if (localStorage.loginFrom) {
                props.history.push(localStorage.loginFrom);
            } else {
                props.history.push("/home");
            }
            // Remove from local storage
            localStorage.removeItem("loginFrom");
        }
    }, [user, props]);

    const getORCID = () => {
        const url = config.ORCID.AUTH_URI;
        //console.log(url)
        //open ORCiD login page
        window.open(url, "_self")
    }
    const HandleMessages = (message) => {
        // Do stuff
        //console.log("got mes", message)
        const data = message;
        const userData = {
            firstname: data.given_name,
            lastname: data.family_name,
            email: data.sub + "@orcid.org",
            socialtype: 'orcid',
            password: data.sub
        };

        //clean up error messages
        dispatch(cleanupMessages());
        //orcid login
        const status = "active";
        if (!userData.lastname) {
            //is optional in ORCiD
            userData.lastname = 'unknown';
        }
        userData.status = status;

        dispatch(socialLogin(userData));
    }

    const closeMsgModal = () => {
        //clean up error messages
        dispatch(cleanupMessages());
    }
    useEffect(() => {
        if (props.location && props.location.hash) {
            const parsed = queryString.parse(props.location.hash);
            //console.log("parsed", parsed.id_token)
            if (parsed.id_token) {
                const decoded = jwt_decode(parsed.id_token);
                HandleMessages(decoded);
            }
        } else {
            getORCID();
        }
    }, [props]);

    return (
        <>
            <LoaderDialog loading={page.submitting_form} text="Verifying email..." />
            <MessageDialog isOpen={messages.sociallogin ? true : false} message={messages.sociallogin} handleClickClose={closeMsgModal} />
            <MessageDialog isOpen={errors.sociallogin ? true : false} message={errors.sociallogin} handleClickClose={closeMsgModal} className='modal-danger' />
        </>
    );
}

export default OrcidLogin;