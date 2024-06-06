import React from 'react';
import { Card, CardBody, CardText, CardTitle } from 'reactstrap';

const OrcidLoginHelp = (props) => {

  return (
    <>
      <Card color="light" outline className='shadow p-3 mb-5 bg-white rounded'>
        <CardBody>
          <CardTitle className='nmdc-header-orcid-login-help-title' tag="h5">
            ORCID Account Integration
          </CardTitle>
          <CardText className='nmdc-header-orcid-login-help-text'>
            <p>
              NMDC EDGE requires an ORCID iD to log in. When logged in you have access to features such as uploading
              files and the ability to create and manage workflow runs.
            </p>
            <p>
              Click the "ORCID Login" button, to either register for an ORCID iD or, if you
              already have one, to sign into your ORCID account, then grant permission for NMDC EDGE to access your
              ORCID iD. This allows us to verify your identity and securely connect to
              your ORCID iD. Additionally, we may use information, such as your name and email, to associate your
              ORCID record with your NMDC EDGE workflow runs.
            </p>
            <p>Learn more about <a href="https://orcid.org/blog/2017/02/20/whats-so-special-about-signing">what's so special about signing in.</a></p>
          </CardText>
        </CardBody>
      </Card>
    </>
  )
}

export default OrcidLoginHelp