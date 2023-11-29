import React, { useState, useEffect } from 'react';
import { Col, Row, Badge } from 'reactstrap';

import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import { getData } from '../../util';

const columns = [
    { title: 'Project', field: 'name', filterPlaceholder: 'Project filter', tooltip: 'Project name', grouping: false, sorting: false },
   // { title: 'Owner', field: 'owner', editable: 'never', tooltip: 'Project owner', sorting: false },
    { title: 'Type', field: 'type', editable: 'never', sorting: false },
    {
        title: 'Status', field: 'status', grouping: false, sorting: false,
        render: rowData => { return <Badge color={projectStatusColors[rowData.status]}>{projectStatusNames[rowData.status]}</Badge> },
        lookup: { 'in queue': 'In queue', 'running': 'Running', 'failed': 'Failed', 'rerun': 'Re-run', 'complete': 'Complete', 'submitted': 'Submitted' }
    },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', hidden: false, filtering: false, grouping: false, sorting: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false, sorting: false },
];

function JobQueue(props) {
    const [tableData, setTableData] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        function getProjects() {
            setLoading(true);
            let url = "/auth-api/user/project/queue";
            getData(url)
                .then(data => {
                    let projects = data.map(obj => {
                        //console.log(obj)
                        let rObj = {};
                        rObj['id'] = obj._id;
                        rObj['name'] = obj.name;
                        rObj['owner'] = obj.owner;
                        rObj['type'] = obj.type;
                        rObj['status'] = obj.status;
                        rObj['created'] = obj.created;
                        rObj['updated'] = obj.updated;

                        return rObj;
                    });
                    setTableData(projects);
                    setLoading(false);
                })
                .catch(err => {
                    setLoading(false);
                    alert(err);
                });
        }
        //refresh table every 30 seconds
        getProjects();
        const timer = setInterval(() => {
            getProjects();
        }, 30000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="animated fadeIn">
            <Row>
                <Col xl={1}></Col>
                <Col xl={10}>

                    <MuiThemeProvider theme={theme}>
                        <MaterialTable
                            isLoading={loading}
                            columns={columns}
                            data={tableData}
                            title="Job Queue"
                            icons={tableIcons}
                            options={{
                                grouping: false,
                                selection: false,
                                pageSize: 10,
                                pageSizeOptions: [10, 20, 50, 100],
                                addRowPosition: 'first',
                                columnsButton: false,
                                actionsColumnIndex: 5,
                                emptyRowsWhenPaging: false,
                                showTitle: true,
                            }}

                            localization={{
                                body: {
                                    emptyDataSourceMessage: "Job queue is empty",
                                },
                                pagination: {
                                    labelRowsSelect: "jobs per page"
                                }
                            }}
                        />
                    </MuiThemeProvider>
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default JobQueue;