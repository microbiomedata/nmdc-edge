import React, { useState, useEffect } from 'react';
import { Redirect } from 'react-router-dom'
import { Col, Row, Badge } from 'reactstrap';

import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import RefreshIcon from '@material-ui/icons/Refresh';
import ExploreIcon from '@material-ui/icons/Explore';
import { getData } from '../../util';

const columns = [
    { title: 'Project', field: 'name', filterPlaceholder: 'Project filter', tooltip: 'Project name', grouping: false },
    { title: 'Description', field: 'desc', hidden: true, grouping: false },
    { title: 'Owner', field: 'owner', editable: 'never', tooltip: 'Project owner' },
    { title: 'Type', field: 'type', editable: 'never' },
    {
        title: 'Status', field: 'status', grouping: false,
        render: rowData => { return <Badge color={projectStatusColors[rowData.status]}>{projectStatusNames[rowData.status]}</Badge> },
        lookup: { 'in queue': 'In queue', 'running': 'Running', 'failed': 'Failed', 'rerun': 'Re-run', 'complete': 'Complete' }
    },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', hidden: false, filtering: false, grouping: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false },
];

function AllProjects(props) {
    const [tableData, setTableData] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        getProjects();
    }, []);


    const getProjects = () => {
        setLoading(true);
        let url = "/auth-api/user/project/alllist";
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
                    rObj['desc'] = obj.desc;
                    rObj['code'] = obj.code;

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
                            title="All Projects Available to Me"
                            icons={tableIcons}
                            options={{
                                grouping: false,
                                selection: true,
                                pageSize: 10,
                                pageSizeOptions: [10, 20, 50, 100],
                                addRowPosition: 'first',
                                columnsButton: true,
                                actionsColumnIndex: 5,
                                emptyRowsWhenPaging: false,
                                showTitle: true,
                            }}
                            //onRowClick={((evt, selectedRow) => { })}

                            actions={[
                                {
                                    icon: () => <RefreshIcon />,
                                    tooltip: 'Refresh Data',
                                    isFreeAction: true,
                                    onClick: () => getProjects(),
                                },
                            ]}
                            detailPanel={[
                                {
                                    icon: () => <ExploreIcon />,
                                    tooltip: 'Go to project result page',
                                    render: rowData => {
                                        return <Redirect to={"/user/project?code=" + rowData.code} />
                                    },
                                },
                            ]}
                        />
                    </MuiThemeProvider>
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default AllProjects;