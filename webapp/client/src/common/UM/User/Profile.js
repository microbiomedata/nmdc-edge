import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { update, cleanupMessages } from "../../../redux/actions/userActions";
import { Col, Row, Form, Button, ButtonGroup, InputGroup, InputGroupAddon, InputGroupText, Input } from 'reactstrap';

import { useForm } from "react-hook-form";
import CIcon from '@coreui/icons-react';
import { ToastContainer } from 'react-toastify';
import { notify } from "../../util";
import 'react-toastify/dist/ReactToastify.css';
import config from "../../../config";

function Profile(props) {
    const dispatch = useDispatch();
    const user = useSelector(state => state.user);
    const updateErrors = useSelector(state => state.errors);
    const messages = useSelector(state => state.messages);
    const [notification, setNotification] = useState(user.notification);

    const { register, handleSubmit, formState: { errors }, watch, setValue, clearErrors } = useForm({
    });

    const firstnameReg = {
        ...register("firstname", {
            required: "Please enter your first name",
            pattern: { value: /^[A-Za-z]+$/, message: 'Your name must be composed only with letters' }
        })
    };
    const lastnameReg = {
        ...register("lastname", {
            required: "Please enter your last name",
            pattern: { value: /^[A-Za-z]+$/, message: 'Your name must be composed only with letters' }
        })
    };

    const emailReg = {
        ...register("mailto", {
            required: notification === 'on' && 'Email is required',
            pattern: { // Validation pattern
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i,
                message: 'Invalid email address'
            }
        })
    };

    useEffect(() => {
        setValue('firstname', user.profile.firstname);
        setValue('lastname', user.profile.lastname);
        setValue('mailto', user.profile.mailto);
        setNotification(user.profile.notification);
    }, [user, setValue]);

    const onReset = e => {
        //clean up error/message
        dispatch(cleanupMessages());
        setValue('firstname', user.profile.firstname);
        setValue('lastname', user.profile.lastname);
        setValue('mailto', user.profile.mailto);
        setNotification(user.profile.notification);
        clearErrors();
    };

    const onSubmit = data => {
        //clean up error/message
        dispatch(cleanupMessages());
        const newUser = {
            firstname: data.firstname,
            lastname: data.lastname,
            mailto: data.mailto,
            notification: notification
        };

        dispatch(update(newUser));
    };

    useEffect(() => {
        if (updateErrors.update) {
            notify("error", "Update failed! " + updateErrors.update);
        }
    }, [updateErrors.update]);

    useEffect(() => {
        if (notification !== 'on') {
            clearErrors();
        }
    }, [notification]);

    useEffect(() => {
        if (messages.update) {
            notify("success", messages.update);
        }
        //clean up error/message
        dispatch(cleanupMessages());
    }, [messages.update]);

    return (
        <div className="app-body flex-row align-items-center">
            <ToastContainer />
            <Row className="justify-content-center">
                <Col sm="12" md="8">
                    <Form onSubmit={handleSubmit(onSubmit)}>
                        <h4 className="pt-3">Profile</h4>
                        <hr></hr>

                        <InputGroup className="mb-3">
                            <InputGroupAddon addonType="prepend">
                                <InputGroupText>
                                    <CIcon name="cil-user" />
                                </InputGroupText>
                            </InputGroupAddon>
                            <Input type="text" name="email" placeholder={user.profile.email} disabled />
                        </InputGroup>

                        <InputGroup className="mb-3">
                            <InputGroupAddon addonType="prepend">
                                <InputGroupText> First Name </InputGroupText>
                            </InputGroupAddon>
                            <Input type="text" name="firstname"
                                onChange={firstnameReg.onChange}
                                innerRef={firstnameReg.ref}
                            />
                        </InputGroup>
                        {errors.firstname && <p className="edge-form-input-error">{errors.firstname.message}</p>}
                        <InputGroup className="mb-3">
                            <InputGroupAddon addonType="prepend">
                                <InputGroupText> Last Name </InputGroupText>
                            </InputGroupAddon>
                            <Input type="text" name="lastname"
                                onChange={lastnameReg.onChange}
                                innerRef={lastnameReg.ref}
                            />
                        </InputGroup>
                        {errors.lastname && <p className="edge-form-input-error">{errors.lastname.message}</p>}
                        {config.EMAIL.IS_ENABLED &&
                            <>
                                <InputGroup className="mb-3">
                                    <InputGroupAddon addonType="prepend">
                                        <InputGroupText>
                                            Email
                                        </InputGroupText>
                                    </InputGroupAddon>
                                    <Input type="text" name="mailto" placeholder="Email" 
                                        onChange={(e) => {
                                            emailReg.onChange(e); // method from hook form register
                                            dispatch(cleanupMessages()); // your method
                                        }}
                                        innerRef={emailReg.ref}
                                    />
                                </InputGroup>
                                {errors.mailto && <p className="edge-form-input-error">{errors.mailto.message}</p>}
                                <br></br>
                                <b >Project Status Notification</b>
                                <br></br>
                                <div className="d-none d-sm-inline-block">
                                    <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                        <Button color="outline-primary" onClick={() => setNotification('on')} active={notification === 'on'}>On</Button>
                                        <Button color="outline-primary" onClick={() => setNotification('off')} active={notification === 'off'}>Off</Button>
                                    </ButtonGroup></div><br /><br />
                                <br></br>
                            </>
                        }
                        <div className="edge-center">
                            <Button color="success" type="submit" >Save Changes</Button>{' '}
                            <Button color="secondary" onClick={onReset} >Reset</Button>
                        </div>
                        <br></br>
                    </Form>
                </Col>
            </Row>
        </div>
    );
}

export default Profile;
