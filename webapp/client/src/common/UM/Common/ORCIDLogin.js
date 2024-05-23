import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { popupWindow } from '../../util';
import { socialLogin, cleanupMessages } from "../../../redux/actions/userActions";
import { LoaderDialog, MessageDialog } from '../../Dialogs';
import config from "../../../config";

export function ORCIDLogin(props) {
    const dispatch = useDispatch();
    const errors = useSelector(state => state.errors);
    const messages = useSelector(state => state.messages);
    const page = useSelector(state => state.page);

    const getORCID = () => {
        const url = config.ORCID.AUTH_URI;
        //console.log(url)
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
        getORCID();
    }, []);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            <LoaderDialog loading={page.submitting_form} text="Verifying email..." />
            <MessageDialog isOpen={messages.sociallogin ? true : false} message={messages.sociallogin} handleClickClose={closeMsgModal} />
            <MessageDialog isOpen={errors.sociallogin ? true : false} message={errors.sociallogin} handleClickClose={closeMsgModal} className='modal-danger' />
        </>
    );
}