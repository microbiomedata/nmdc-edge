import React from 'react';
import { Badge, Col, Row } from 'reactstrap';
import UserTable from './UserTable';

function Users(props) {
    return (
        <div className="animated fadeIn">
            <Row >
                <Col xl={1}></Col>
                <Col xl={10}>
                    <Badge href="#" color="danger" pill>Admin tool</Badge>
                </Col>
            </Row>
            <br></br>
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <UserTable title={"Manage Users"} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Users;