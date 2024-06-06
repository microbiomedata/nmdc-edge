import React, { useState, useEffect } from 'react';
import { Col, Row, Badge } from 'reactstrap';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import RefreshIcon from '@material-ui/icons/Refresh';
import { BsFolderSymlink } from "react-icons/bs";
import Tooltip from '@material-ui/core/Tooltip';
import IconButton from "@material-ui/core/IconButton";
import { getData } from '../../util';

function ProjectList(props) {
    const [tableData, setTableData] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        getProjects();
    }, []);

    const getProjects = () => {
        setLoading(true);
        let url = "/api/project/list";
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
                    <div style={{ maxWidth: "100%" }}>

                        <MuiThemeProvider theme={theme}>
                            <MaterialTable
                                isLoading={loading}
                                columns={[
                                    { title: 'Project', field: 'name', filterPlaceholder: 'Project filter', tooltip: 'Project name', grouping: false },
                                    { title: 'Description', field: 'desc', hidden: true, grouping: false },
                                    //{ title: 'Owner', field: 'owner', editable: 'never', tooltip: 'Project owner' },
                                    { title: 'Type', field: 'type', editable: 'never' },
                                    {
                                        title: 'Status', field: 'status', grouping: false,
                                        render: rowData => { return <Badge color={projectStatusColors[rowData.status]}>{projectStatusNames[rowData.status]}</Badge> },
                                        lookup: { 'in queue': 'In queue', 'running': 'Running', 'failed': 'Failed', 'rerun': 'Re-run', 'complete': 'Complete' }
                                    },
                                    {
                                        title: "Result",
                                        render: (rowData) => {
                                            const button = (
                                                <Tooltip title={'Go to result page'}>
                                                    <span>
                                                        <IconButton
                                                            onClick={() => {
                                                                props.history.push("/public/project?code=" + rowData.code);
                                                            }}
                                                        >
                                                        <BsFolderSymlink style={{ color: '#4f3B80' }} />
                                                        </IconButton></span>
                                                </Tooltip>
                                            );
                                            return button;
                                        }
                                    },
                                    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', hidden: false, filtering: false, grouping: false },
                                    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false },
                                ]}
                                data={tableData}
                                title={"Public Projects"}
                                icons={tableIcons}
                                options={{
                                    grouping: false,
                                    pageSize: 10,
                                    pageSizeOptions: [10, 20, 50, 100],
                                    addRowPosition: 'first',
                                    columnsButton: true,
                                    actionsColumnIndex: 8,
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
                            />
                        </MuiThemeProvider>
                    </div>
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default ProjectList;