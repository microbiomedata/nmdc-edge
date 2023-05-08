import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { withRouter } from "react-router-dom";
import { register, cleanupMessages } from "../../../redux/actions/userActions";
import { Card, CardBody, Col, Container, Row } from 'reactstrap';
import { LoaderDialog, MessageDialog } from "../../Dialogs";
import RegisterForm from "./forms/RegisterForm";

function Register(props) {

  const dispatch = useDispatch();
  const user = useSelector(state => state.user);
  const registerErrors = useSelector(state => state.errors);
  const messages = useSelector(state => state.messages);
  const page = useSelector(state => state.page);

  useEffect(() => {
    dispatch(cleanupMessages());
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // If logged in and user navigates to Login page, should redirect them to dashboard
    if (user.isAuthenticated) {
      props.history.push("/home");
    }
  }, [props, user]);// eslint-disable-line react-hooks/exhaustive-deps


  const handleValidSubmit = data => {
    dispatch(cleanupMessages());

    var status = "active";
    if (process.env.REACT_APP_EMAIL_NOTIFICATION === 'true') {
      status = "inactive";
    }
    const newUser = {
      firstname: data.firstname,
      lastname: data.lastname,
      email: data.email,
      password: data.password,
      password2: data.password2,
      status: status
    };
    //console.log(newUser)
    dispatch(register(newUser));
  };

  const closeMsgModal = () => {
    props.history.push("/login");
  }

  return (
    <div className="app-body flex-row align-items-center">
      <LoaderDialog loading={page.submitting_form} text="Verifying email..." />
      <Container>
        <Row className="justify-content-center">
          <Col md="6">
            <Card className="p-4 um-card">
              <CardBody className="p-4">
                {registerErrors.register && <p className="edge-form-input-error">{registerErrors.register}</p>}
                <RegisterForm errors={registerErrors} loading={page.submitting_form}
                  onSubmit={handleValidSubmit} />
                <MessageDialog isOpen={messages.register ? true : false} message={messages.register} handleClickClose={closeMsgModal} />
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default withRouter(Register);
