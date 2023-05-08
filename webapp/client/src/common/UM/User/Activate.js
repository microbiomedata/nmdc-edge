import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { activate, getActivationLink, cleanupMessages } from "../../../redux/actions/userActions";
import { Form, Input, Button, Card, CardBody, Col, Container, InputGroup, InputGroupAddon, InputGroupText, Row } from 'reactstrap';
import { MessageDialog } from '../../Dialogs';
import { useForm } from "react-hook-form";
import CIcon from '@coreui/icons-react';

const queryString = require('query-string');

function Activate(props) {
  const dispatch = useDispatch();
  const user = useSelector(state => state.user);
  const activateErrors = useSelector(state => state.errors);
  const messages = useSelector(state => state.messages);

  const { register, handleSubmit, formState: { errors } } = useForm({
    mode: 'onChange',
  });

  const emailReg = {
    ...register("email", {
      required: 'Email is required',
      pattern: { // Validation pattern
        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i,
        message: 'Invalid email address'
      }
    })
  };

  useEffect(() => {
    // If logged in and user navigates to this page, should redirect them to home page
    if (user.isAuthenticated) {
      props.history.push("/home");
    }

    dispatch(cleanupMessages());
    const parsed = queryString.parse(props.location.search);

    if (parsed.email && parsed.token) {
      const userData = {
        email: parsed.email,
        password: parsed.token,
      };

      dispatch(activate(userData));
    }
  }, []);// eslint-disable-line react-hooks/exhaustive-deps


  const closeMsgModal = () => {
    props.history.push("/login");
  }

  const onSubmit = data => {
    dispatch(cleanupMessages());

    const userData = {
      email: data.email,
    };
    dispatch(getActivationLink(userData));
  };

  return (
    <div className="app-body flex-row align-items-center">
      {messages.activate ?
        <MessageDialog isOpen={messages.activate ? true : false} message={messages.activate} handleClickClose={closeMsgModal} />
        : (
          <Container>
            <Row className="justify-content-center">
              <Col md="6">
                <Card className="p-4 um-card">
                  <CardBody>
                    <Form onSubmit={handleSubmit(onSubmit)}>
                      <span className="red-text">
                        {messages.getActivationLink}
                      </span>
                      <h1>Activate Account</h1>
                      <span className="red-text">
                        {activateErrors.activate}
                      </span>
                      <InputGroup className="mb-3">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText>
                            <CIcon name="cil-user" />
                          </InputGroupText>
                        </InputGroupAddon>
                        <Input type="text" name="email" placeholder="Email"
                          onChange={(e) => {
                            emailReg.onChange(e); // method from hook form register
                            dispatch(cleanupMessages()); // your method
                          }}
                          innerRef={emailReg.ref}
                        />
                      </InputGroup>
                      {errors.email && <p className="edge-form-input-error">{errors.email.message}</p>}
                      <Row>
                        <Col>
                          <Button color="primary" type="submit" className="px-4" block>Get Activation Link</Button>
                        </Col>
                      </Row>
                    </Form>
                  </CardBody>
                </Card>
              </Col>
            </Row>
          </Container>
        )}
    </div >
  );
}

export default Activate;
