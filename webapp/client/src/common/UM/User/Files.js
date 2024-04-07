import React, { useState } from 'react';
import { Col, Row, } from 'reactstrap';
import FileTable from '../Common/FileTable';
import Uploadfiles from './Uploadfiles';

function Files(props) {
    const [refreshTable, setRefreshTable] = useState(0);

    const reloadTableData = () => {
        setRefreshTable(refreshTable + 1);
    }

    return (
        <div className="animated fadeIn">
            <Uploadfiles reloadTableData={reloadTableData} />
            <br></br>
            <br></br>
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>
                    <FileTable tableType='user' title={"My Uploads"} refresh={refreshTable} {...props} />
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Files;