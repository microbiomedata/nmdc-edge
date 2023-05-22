import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { resetpassword, getResetpasswordLink, cleanupMessages } from "../../../redux/actions/userActions";
import { Form, Input, Button, Card, CardBody, Col, Container, InputGroup, InputGroupAddon, InputGroupText, Row } from 'reactstrap';
import { useForm } from "react-hook-form";
import CIcon from '@coreui/icons-react';
import { MessageDialog } from '../../Dialogs';
import { MyTooltip } from '../../MyTooltip';
import { UM_messages } from '../Common/Defaults';

const queryString = require('query-string');

function Resetpassword(props) {
  const [reset, setReset] = useState(false);
  const [email, setEmail] = useState();
  const [password, setPassword] = useState();

  const dispatch = useDispatch();
  const user = useSelector(state => state.user);
  const resetpasswordErrors = useSelector(state => state.errors);
  const messages = useSelector(state => state.messages);

  const { register, handleSubmit, formState: { errors }, watch, setValue} = useForm({
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

  //componentDidMount()
  useEffect(() => {
    // If logged in and user navigates to this page, should redirect them to home page
    if (user.isAuthenticated) {
      props.history.push("/home");
    }

    dispatch(cleanupMessages());
    const parsed = queryString.parse(props.location.search);
    //console.log(parsed);

    if (parsed.email && parsed.token) {
      setEmail(parsed.email);
      setPassword(parsed.token);
      setReset(true);
      //set hook form email value to avoid onSubmit error
      setValue("email", parsed.email, { shouldValidate: true });
    }
  }, [props, user]);// eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = (data) => {
    //clean up error/message
    dispatch(cleanupMessages());

    if (data.newpassword) {
      //reset password
      const userData = {
        email: email,
        password: password,
        newpassword: data.newpassword,
        newpassword2: data.newpassword2,
      };
      
      dispatch(resetpassword(userData));
    } else {
      const userData = {
        email: data.email,
      };

      dispatch(getResetpasswordLink(userData));
    }
  };

  const closeMsgModal = () => {
    props.history.push("/login");
  }

  return (
    <div className="app-body flex-row align-items-center">
      <Container>
        <Row className="justify-content-center">
          <Col md="6">
            <Card className="p-4 um-card">
              <CardBody>
                <Form onSubmit={handleSubmit(onSubmit)} >
                  <span className="red-text">
                    {resetpasswordErrors.resetpassword}
                  </span>
                  <span className="red-text">
                    {messages.getResetpasswordLink}
                  </span>
                  <h1>Reset Password</h1>
                  {reset ? (
                    <div>
                      <InputGroup className="mb-3">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText>
                            <CIcon name="cil-lock-locked" />
                          </InputGroupText>
                        </InputGroupAddon>
                        <Input type="password" name="newpassword" placeholder="Password"
                          {...register("newpassword", {
                            required: "Password is required",
                            minLength: { value: 8, message: 'Must be at least 8 characters long' },
                            validate: {
                              hasUpperCase: (value) => /[A-Z]/.test(value) || 'Must contain at least one uppercase letter',
                              hasLowerCase: (value) => /[a-z]/.test(value) || 'Must contain at least one lowercase letter',
                              hasNumber: (value) => /[0-9]/.test(value) || 'Must contain at least one number',
                              hasSpecialChar: (value) => /[^A-Za-z0-9 ]/.test(value) || 'Must contain at least one special character',
                            }
                          })}
                        />
                      </InputGroup>
                      {errors.newpassword && <p className="edge-form-input-error">{errors.newpassword.message}
                        <MyTooltip id='passwordRegister' tooltip={UM_messages.passwordHints} showTooltip={true} />
                      </p>}
                      <InputGroup className="mb-4">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText>
                            <CIcon name="cil-lock-locked" />
                          </InputGroupText>
                        </InputGroupAddon>
                        <Input type="password" name="newpassword2" placeholder="Repeat password"
                          {...register("newpassword2", {
                            validate: value =>
                              value === watch('newpassword') || "The passwords do not match"
                          })}
                        />
                      </InputGroup>
                      {errors.newpassword2 && <p className="edge-form-input-error">{errors.newpassword2.message}</p>}
                      <Button color="success" type="submit" block>Reset Password</Button>
                    </div>
                  ) : (<div>
                    <span className="red-text">
                      {resetpasswordErrors.resetpasswordLink}
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
                        <Button color="primary" type="submit" className="px-4" block>Get Resetpassword Link</Button>
                      </Col>
                    </Row>
                  </div>
                    )}
                </Form>
              </CardBody>
            </Card>
            <MessageDialog isOpen={messages.resetpassword ? true : false} message={messages.resetpassword} handleClickClose={closeMsgModal} />
          </Col>
        </Row>
      </Container>
    </div >
  );
}

export default Resetpassword;
