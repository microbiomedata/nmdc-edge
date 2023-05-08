import React, { useState } from 'react';
import { Button } from 'reactstrap';

import { useDispatch, useSelector } from 'react-redux';

import { popupWindow } from '../../util';

import { socialLogin, cleanupMessages } from "../../../redux/actions/userActions";
import { LoaderDialog, ConfirmDialogNoHeader, MessageDialog } from '../../Dialogs';

export function ORCIDLogin(props) {
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

    const getORCID = () => {
        //ORICD config
        const url = process.env.REACT_APP_ORCID_AUTH_URL;
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
            <p className="text-muted">Use your ORCID account for faster login or registration</p>

            <Button color="success" className="px-4" block onClick={e => getORCID()}>Login with ORCiD</Button>
        </>
    );
}