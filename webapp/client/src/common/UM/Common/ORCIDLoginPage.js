import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Col, Container, Row } from 'reactstrap';
import { ORCIDLogin } from '../Common/ORCIDLogin';
import OrcidLoginHelp from './OrcidLoginHelp';

function ORCIDLoginPage(props) {
  const user = useSelector(state => state.user);

  useEffect(() => {
    if (user.isAuthenticated) {
      if (props.location.state) {
        props.history.push(props.location.state.from);
      } else {
        props.history.push("/home");
      }
    }
  }, [user, props]);

  return (
    <div style={{paddingTop: '80px'}} className="app-body flex-row align-items-center">
      <Container>
        <Row className="justify-content-center">
          <Col md={6}>
            <OrcidLoginHelp />
            <ORCIDLogin />
          </Col>
        </Row>
      </Container>
    </div >
  );
}

export default ORCIDLoginPage;
