import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { login, cleanupMessages } from "../../../redux/actions/userActions";
import { Form, Input, Button, Card, CardBody, CardGroup, Col, Container, InputGroup, InputGroupAddon, InputGroupText, Row } from 'reactstrap';

import { useForm } from "react-hook-form";

import CIcon from '@coreui/icons-react';
import { MyTooltip } from '../../MyTooltip';
import { UM_messages } from '../Common/Defaults';
import { ORCIDLogin } from '../Common/ORCIDLogin';
import config from "../../../config";

function Login(props) {
  const dispatch = useDispatch();
  const user = useSelector(state => state.user);
  const loginErrors = useSelector(state => state.errors);
  const messages = useSelector(state => state.messages);
  const { register, handleSubmit, formState: { errors } } = useForm({
    mode: 'onChange',
  });

  const passwordReg = {
    ...register("password", {
      required: " Password is required",
      minLength: { value: 8, message: 'Must be at least 8 characters long' },
      validate: {
        hasUpperCase: (value) => /[A-Z]/.test(value) || 'Must contain at least one uppercase letter',
        hasLowerCase: (value) => /[a-z]/.test(value) || 'Must contain at least one lowercase letter',
        hasNumber: (value) => /[0-9]/.test(value) || 'Must contain at least one number',
        hasSpecialChar: (value) => /[^A-Za-z0-9 ]/.test(value) || 'Must contain at least one special character',
      }
    })
  };

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
    //clean up error messages
    dispatch(cleanupMessages());
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (user.isAuthenticated) {
      if (props.location.state) {
        props.history.push(props.location.state.from);
      } else {
        props.history.push("/home");
      }
    }
  }, [user, props]);

  const onSubmit = data => {
    //clean up error messages
    dispatch(cleanupMessages());

    //console.log(data)
    const userData = {
      email: data.email,
      password: data.password
    };
    dispatch(login(userData));
  };

  return (
    <div className="app-body flex-row align-items-center">
      <Container>
        <Row className="justify-content-center">

          <Col md={6}>
            <CardGroup>
              <Card className="p-4 um-card">
                <CardBody>
                  <Form onSubmit={handleSubmit(onSubmit)}>
                    <span className="red-text">
                      {messages.login}
                    </span>
                    <span className="red-text">
                      {loginErrors.login}
                    </span>
                    <h1>Login</h1>
                    <p className="text-muted">Sign In to your account</p>
                    <span className="red-text">
                      {loginErrors.email}
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
                    <span className="red-text">
                      {loginErrors.password}
                    </span>
                    <InputGroup className="mb-4">
                      <InputGroupAddon addonType="prepend">
                        <InputGroupText>
                          <CIcon name="cil-lock-locked" />
                        </InputGroupText>
                      </InputGroupAddon>
                      <Input type="password" name="password" placeholder="Password"
                        onChange={(e) => {
                          passwordReg.onChange(e); // method from hook form register
                          dispatch(cleanupMessages()); // your method
                        }}
                        innerRef={passwordReg.ref}
                      />
                    </InputGroup>
                    {errors.password && <p className="edge-form-input-error">{errors.password.message}
                      <MyTooltip id='passwordRegister' tooltip={UM_messages.passwordHints} showTooltip={true} />
                    </p>}
                    <Row>
                      <Col xs="12">
                        <Button color="primary" type="submit" className="px-4" block>Login</Button>
                      </Col>
                    </Row>
                  </Form>
                  <Row className="justify-content-center">
                  </Row>
                </CardBody>
              </Card>
            </CardGroup>
          </Col>
        </Row>
      </Container>
    </div >
  );
}

export default Login;
