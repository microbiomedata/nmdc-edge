import React from 'react';
import { Card, CardBody, CardText, CardTitle } from 'reactstrap';
import { MdInfo } from "react-icons/md";
import { useSelector } from 'react-redux';

const AppBanner = (props) => {
  const user = useSelector(state => state.user);

  return (
    <span>
      {
        user.isAuthenticated ? (<></>) :
          (
            <div className="nmdc-edge-app-banner">
              <Card
                className="my-2"
                color="info"
                inverse
              >
                <CardBody>
                  <CardText>
                    <CardTitle tag="h4">
                      <MdInfo size={28} /> <b>Announcement</b>
                    </CardTitle>
                    The Email/Password login is disabled. NMDC EDGE now requires an ORCID iD to log in. 
                    Click the "ORCID LOGIN" button, to either register for an ORCID iD or, if you 
                    already have one, to sign into your ORCID account, then grant permission for NMDC EDGE 
                    to access your ORCID iD.

                    <br></br><br></br>
                    For users with existing projects under an Email/Password account, you will be able to 
                    migrate your old projects and uploads to your newly created ORCID iD account by clicking 
                    the "Import Old Projects/Uploads with Email/Password" button.

                  </CardText>
                </CardBody>
              </Card>
            </div>
          )
      }
    </span>
  );
}

export default AppBanner