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
                    Due to a fire at the San Diego Supercomputing Center, nmdc-edge is down. There is no access to user projects and no new projects can be created. We do not know how long it will take for this to be resolved. We will update this message when we get more information
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