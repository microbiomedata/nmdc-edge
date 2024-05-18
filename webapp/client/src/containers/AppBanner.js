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
                    We disabled the User/Password login.

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