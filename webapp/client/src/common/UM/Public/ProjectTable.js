import React, { useState, useEffect } from 'react';
import { Redirect } from 'react-router-dom'
import { Col, Row, Badge } from 'reactstrap';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import RefreshIcon from '@material-ui/icons/Refresh';
import ExploreIcon from '@material-ui/icons/Explore';
import { getData, postData } from '../../util';

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

function ProjectTable(props) {
    const [tableData, setTableData] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        getProjects();
    }, []);

    const getProjects = () => {
        setLoading(true);
        let url = "/api/project/list";
        if (props.projectType && props.projectType === 'batch') {
            url = "/api/project/batch/list";
        }
        const projData = {
            code: props.code,
        };
        postData(url, projData)
            //getData(url, projData)
            .then(data => {
                setTableData(data);
                setLoading(false);
            })
            .catch(err => {
                setLoading(false);
                alert(err);
            });
    }

    return (
        <MuiThemeProvider theme={theme}>
            <MaterialTable
                localization={{ body: { emptyDataSourceMessage: props.tableNoRecordsMsg ? props.tableNoRecordsMsg : 'No records to display' } }}
                isLoading={loading}
                columns={columns}
                data={tableData}
                title={props.title}
                icons={tableIcons}
                options={{
                    grouping: props.tableGrouping ? props.tableGrouping : false,
                    pageSize: 10,
                    pageSizeOptions: [10, 20, 50, 100],
                    emptyRowsWhenPaging: false,
                    showTitle: props.tableShowTitle ? props.tableShowTitle : false,
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
                            return <Redirect to={"/public/project?code=" + rowData.code} />
                        },
                    },
                ]}
            />
        </MuiThemeProvider>
    );
}

export default ProjectTable;