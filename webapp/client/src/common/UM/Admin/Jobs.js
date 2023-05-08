import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Col, Row, Badge } from 'reactstrap';

import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { updateProjectAdmin } from "../../../redux/actions/adminActions";
import { ToastContainer } from 'react-toastify';
import { notify, getData } from "../../util";
import 'react-toastify/dist/ReactToastify.css';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import RefreshIcon from '@material-ui/icons/Refresh';

const columns = [
    { title: 'Project', field: 'name', filterPlaceholder: 'Project filter', tooltip: 'Project name', grouping: false, sorting: false },
    { title: 'Owner', field: 'owner', editable: 'never', tooltip: 'Project owner', sorting: false },
    { title: 'Type', field: 'type', editable: 'never', sorting: false },
    {
        title: 'Status', field: 'status', grouping: false, sorting: false,
        render: rowData => { return <Badge color={projectStatusColors[rowData.status]}>{projectStatusNames[rowData.status]}</Badge> },
        lookup: { 'in queue': 'In queue', 'running': 'Running', 'failed': 'Failed', 'rerun': 'Re-run', 'complete': 'Complete', 'submitted': 'Submitted' }
    },
    { title: 'Job Priority', field: 'jobpriority', type: 'numeric' },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', hidden: false, filtering: false, grouping: false, sorting: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false, sorting: false },
];

function Jobs(props) {
    const dispatch = useDispatch();
    const user = useSelector(state => state.user);
    const errors = useSelector(state => state.errors);
    const [tableData, setTableData] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (user.profile.type !== "admin") {
            props.history.push("/home");
        } else {
            getJobs();
        }
    }, [props, user]);

    const getJobs = () => {
        setLoading(true);
        let url = "/auth-api/admin/project/queue";
        getData(url)
            .then(data => {
                let projects = data;
                setTableData(projects);
                setLoading(false);
            })
            .catch(err => {
                setLoading(false);
                alert(err);
            });
    }

    const myUpdateJob = (newJob) => {
        console.log(newJob)

        dispatch(updateProjectAdmin(newJob));
        setTimeout(() => afterActionSubmit('update job' + newJob.name), 500);
    }

    const afterActionSubmit = (action) => {
        if (errors && Object.values(errors).length >= 1) {
            notify("error", action + " failed! ");
            if (errors.email) {
                notify("error", errors.email);
            }
            if (errors.error) {
                notify("error", errors.error);
            }
        } else {
            notify("success", action + " successfully!");
            getJobs();
        }
    }

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
                    <ToastContainer />
                    <MuiThemeProvider theme={theme}>
                        <MaterialTable
                            isLoading={loading}
                            columns={columns}
                            data={tableData}
                            title="Manage Jobs"
                            icons={tableIcons}
                            options={{
                                grouping: false,
                                selection: false,
                                pageSize: 10,
                                pageSizeOptions: [10, 20, 50, 100],
                                addRowPosition: 'first',
                                columnsButton: false,
                                actionsColumnIndex: 7,
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
                            editable={{
                                onRowUpdate: (newData, oldData) =>
                                    new Promise((resolve, reject) => {
                                        setTimeout(() => {
                                            myUpdateJob(newData);
                                            resolve()
                                        }, 1000)
                                    }),
                            }}
                            actions={[
                                {
                                    icon: () => <RefreshIcon />,
                                    tooltip: 'Refresh Data',
                                    isFreeAction: true,
                                    onClick: () => getJobs(),
                                }
                            ]}
                        />
                    </MuiThemeProvider>
                </Col>
            </Row>
            <br></br>
        </div>
    );
}

export default Jobs;