import React, { useEffect, useState } from 'react'
import { LoaderDialog } from '../common/Dialogs';
import { postData } from "../common/util";
import {
  Button, Modal, ModalHeader, ModalBody, ModalFooter, Form, Input, InputGroup, InputGroupAddon, InputGroupText
} from 'reactstrap';

import { useForm } from "react-hook-form";

import CIcon from '@coreui/icons-react';
import { MyTooltip } from '../common/MyTooltip';
import { UM_messages } from '../common/UM/Common/Defaults';


const ImportOldData = (props) => {
  const [submitting, setSubmitting] = useState(false)

  const { register, handleSubmit, formState: { errors }, clearErrors } = useForm({
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

  //submit button clicked
  const onSubmit = (data) => {
    let url = "/auth-api/user/import-old-data";
    setSubmitting(true);
    const userData = {
      email: data.email,
      password: data.password
    };
    // submit to server via api
    postData(url, userData)
      .then((ret) => {
        setSubmitting(false)
          props.handleSuccess();
      })
      .catch((error) => {
        setSubmitting(false);
        alert(JSON.stringify(error));
      })
  }
  useEffect(() => {
    clearErrors();
  }, [props]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Modal isOpen={props.isOpen} centered>
      <LoaderDialog loading={submitting === true} text="Submitting..." />
      <Form onSubmit={handleSubmit(onSubmit)}>
        <ModalHeader className="justify-content-center">
          <h4>Import old projects/uploads with email/password</h4>
          {/* <span className="red-text pt-3 edge-text-size-small">
            (Note: this tool will be disabled after June 15)
          </span> */}
        </ModalHeader>
        <ModalBody>
          <p className="text-muted">Your email/password account</p>
          <InputGroup className="mb-3">
            <InputGroupAddon addonType="prepend">
              <InputGroupText>
                <CIcon name="cil-user" />
              </InputGroupText>
            </InputGroupAddon>
            <Input type="text" name="email" placeholder="Email"
              onChange={(e) => {
                emailReg.onChange(e); // method from hook form register
              }}
              innerRef={emailReg.ref}
            />
          </InputGroup>
          {errors.email && <p className="edge-form-input-error">{errors.email.message}</p>}
          <InputGroup className="mb-4">
            <InputGroupAddon addonType="prepend">
              <InputGroupText>
                <CIcon name="cil-lock-locked" />
              </InputGroupText>
            </InputGroupAddon>
            <Input type="password" name="password" placeholder="Password"
              onChange={(e) => {
                passwordReg.onChange(e); // method from hook form register
              }}
              innerRef={passwordReg.ref}
            />
          </InputGroup>
          {errors.password && <p className="edge-form-input-error">{errors.password.message}
            <MyTooltip id='passwordRegister' tooltip={UM_messages.passwordHints} showTooltip={true} />
          </p>}
        </ModalBody>
        <ModalFooter className="justify-content-center">
          <Button color="primary" type="submit">Submit</Button>{' '}
          <Button color="secondary" onClick={props.handleClickClose}>
            Cancel
          </Button>
        </ModalFooter>
      </Form>
    </Modal >
  )
}

export default ImportOldData