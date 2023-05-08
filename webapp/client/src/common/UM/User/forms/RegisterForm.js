import React from 'react';
import { useDispatch } from 'react-redux';
import { cleanupMessages } from "../../../../redux/actions/userActions";
import { Form, Button, InputGroup, InputGroupAddon, InputGroupText, Input } from 'reactstrap';
import { useForm } from "react-hook-form";
import CIcon from '@coreui/icons-react';
import { MyTooltip } from '../../../MyTooltip';
import { UM_messages } from '../../Common/Defaults';

function RegisterForm(props) {
  const dispatch = useDispatch();
  const { register, handleSubmit, formState: { errors }, watch } = useForm({
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

  return (
    <Form onSubmit={handleSubmit(props.onSubmit)}>
      <h1>Register</h1>
      <p className="text-muted"></p>
      <InputGroup className="mb-3">
        <InputGroupAddon addonType="prepend">
          <InputGroupText> First Name </InputGroupText>
        </InputGroupAddon>
        <Input type="text" name="firstname"
          {...register("firstname", {
            required: "Please enter your first name",
            pattern: { value: /^[A-Za-z]+$/, message: 'Your name must be composed only with letters' }
          })}
        />
      </InputGroup>
      {errors.firstname && <p className="edge-form-input-error">{errors.firstname.message}</p>}
      <InputGroup className="mb-3">
        <InputGroupAddon addonType="prepend">
          <InputGroupText> Last Name </InputGroupText>
        </InputGroupAddon>
        <Input type="text" name="lastname"
          {...register("lastname", {
            required: "Please enter your last name",
            pattern: { value: /^[A-Za-z]+$/, message: 'Your name must be composed only with letters' }
          })}
        />
      </InputGroup>
      {errors.lastname && <p className="edge-form-input-error">{errors.lastname.message}</p>}
      <span className="red-text">{props.errors.email}</span>
      <InputGroup className="mb-3">
        <InputGroupAddon addonType="prepend">
          <InputGroupText><CIcon name="cil-user" /></InputGroupText>
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
              hasUpperCase: (value) => /[A-Z]/.test(value) || 'Must contain at lease one uppercase letter',
              hasLowerCase: (value) => /[a-z]/.test(value) || 'Must contain at lease one lowercase letter',
              hasNumber: (value) => /[0-9]/.test(value) || 'Must contain at lease one number',
              hasSpecialChar: (value) => /[^A-Za-z0-9 ]/.test(value) || 'Must contain at lease one special character',
            }
          })}
        />
      </InputGroup>
      {errors.password &&
        <p className="edge-form-input-error">{errors.password.message}
          <MyTooltip id='passwordRegister' tooltip={UM_messages.passwordHints} showTooltip={true} />
        </p>
      }
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
      <Button color="primary" disabled={props.loading} type="submit" block>Create Account</Button>
    </Form>
  );
}

export default RegisterForm;
