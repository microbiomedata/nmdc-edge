import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { withRouter } from "react-router-dom";
import { update, cleanupMessages } from "../../../redux/actions/userActions";
import { Card, CardBody, Col, Container, Row, Form, Button, ButtonGroup, InputGroup, InputGroupAddon, InputGroupText, Input } from 'reactstrap';

import { useForm } from "react-hook-form";
import CIcon from '@coreui/icons-react';
import { ToastContainer } from 'react-toastify';
import { notify } from "../../util";
import 'react-toastify/dist/ReactToastify.css';

function Update(props) {
  const [changePw, setChangePw] = useState(0);

  const dispatch = useDispatch();
  const user = useSelector(state => state.user);
  const updateErrors = useSelector(state => state.errors);
  const messages = useSelector(state => state.messages);

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

  useEffect(() => {
    setValue('firstname', user.profile.firstname);
    setValue('lastname', user.profile.lastname);
    setValue('email', user.profile.email);
  }, [user, setValue]);

  const onReset = e => {
    //clean up error/message
    dispatch(cleanupMessages());
    setValue('firstname', user.profile.firstname);
    setValue('lastname', user.profile.lastname);
    setValue('email', user.profile.email);
    clearErrors();
    setChangePw(0);
  };

  const onSubmit = data => {
    console.log("sub")
    //clean up error/message
    dispatch(cleanupMessages());
    const newUser = {
      firstname: data.firstname,
      lastname: data.lastname,
      email: user.profile.email,
      password: data.password,
      password2: data.password2
    };
    dispatch(update(newUser));
    setChangePw(0);
  };

  const handleCpChange = (changePw) => {
    setChangePw(changePw)
  }

  useEffect(() => {
    if (updateErrors.update) {
      notify("error", "Update failed! " + updateErrors.update);
    }
  }, [updateErrors.update]);

  useEffect(() => {
    if (messages.update) {
      notify("success", messages.update);
    }
  }, [messages.update]);

  return (
    <div className="app-body flex-row align-items-center">
      <Container>
        <ToastContainer />
        <Row className="justify-content-center">
          <Col md="9" lg="7" xl="6">
            <Card className="mx-4 um-card">
              <CardBody className="p-4">
                <Form onSubmit={handleSubmit(onSubmit)}>
                  <h1>Update Account</h1>
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

                  <InputGroup className="mb-3">
                    <InputGroupAddon addonType="prepend">
                      <InputGroupText>
                        <CIcon name="cil-user" />
                      </InputGroupText>
                    </InputGroupAddon>
                    <Input type="text" name="email" placeholder={user.profile.email} disabled
                    />
                  </InputGroup>
                  <br></br><br></br>

                  <h4>Change password</h4>
                  <div className="d-none d-sm-inline-block">
                    <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                      <Button color="outline-primary" onClick={() => handleCpChange(0)} active={changePw === 0}>No</Button>
                      <Button color="outline-primary" onClick={() => handleCpChange(1)} active={changePw === 1}>Yes</Button>
                    </ButtonGroup></div><br /><br />
                  {changePw === 1 &&
                    <div>
                      <InputGroup className="mb-3">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText>
                            <CIcon name="cil-lock-locked" />
                          </InputGroupText>
                        </InputGroupAddon>
                        <Input type="password" name="password" placeholder="Password"
                          {...register("password", {
                            required: "Please enter a password",
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
                      {errors.password && <p className="edge-form-input-error">{errors.password.message}</p>}
                      <InputGroup className="mb-4">
                        <InputGroupAddon addonType="prepend">
                          <InputGroupText>
                            <CIcon name="cil-lock-locked" />
                          </InputGroupText>
                        </InputGroupAddon>
                        <Input type="password" name="password2" placeholder="Repeat password"
                          {...register("password2", {
                            validate: value =>
                              value === watch('password') || "The passwords do not match"
                          })}
                        />
                      </InputGroup>
                      {errors.password2 && <p className="edge-form-input-error">{errors.password2.message}</p>}
                    </div>
                  }
                  <Button color="success" type="submit" block>Save Changes</Button>
                  <Button color="secondary" onClick={onReset} block>Reset</Button>
                </Form>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default withRouter(Update);
