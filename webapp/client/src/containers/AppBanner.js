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
                    Please note that NMDC EDGE has experience intermittent issues with running workflows. We are aware of these issues
                    and are actively working to fix them. Thank you for your patience and please reach out at support@microbiomedata.org 
                    if you have specific concerns.
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