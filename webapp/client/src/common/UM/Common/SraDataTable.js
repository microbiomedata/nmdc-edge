import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Redirect } from 'react-router-dom'
import { Badge } from 'reactstrap';
import { updateProjectAdmin } from "../../../redux/actions/adminActions";
import { updateProject, cleanupMessages } from "../../../redux/actions/userActions";
import UserSelector from './UserSelector';
import { ConfirmDialog } from '../../Dialogs';
import startCase from 'lodash.startcase';

import { ToastContainer } from 'react-toastify';
import { notify, getData } from "../../util";
import 'react-toastify/dist/ReactToastify.css';

import MaterialTable, { MTableToolbar } from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, projectStatusColors, projectStatusNames } from '../../table';

import Fab from '@material-ui/core/Fab';
import DeleteIcon from '@material-ui/icons/Delete';
import RefreshIcon from '@material-ui/icons/Refresh';
import PersonAddIcon from '@material-ui/icons/PersonAdd';
import PersonAddDisabledIcon from '@material-ui/icons/PersonAddDisabled';
import LockIcon from '@material-ui/icons/Lock';
import LockOpenIcon from '@material-ui/icons/LockOpen';
import ExploreIcon from '@material-ui/icons/Explore';
import Tooltip from '@material-ui/core/Tooltip';

const columns = [
    { title: 'Name', field: 'name', filterPlaceholder: 'Name filter', tooltip: 'name', grouping: false },
    {
        title: 'Status', field: 'status', editable: 'never', grouping: false,
        render: rowData => { return <Badge color={projectStatusColors[rowData.status]}>{projectStatusNames[rowData.status]}</Badge> },
        lookup: { 'in queue': 'In queue', 'running': 'Running', 'failed': 'Failed', 'rerun': 'Re-run', 'complete': 'Complete' }
    },
    { title: 'Shared', field: 'shared', lookup: { true: 'Yes', false: 'No' }, editable: 'never' },
    { title: 'Public', field: 'public', lookup: { true: 'Yes', false: 'No' } },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', filtering: false, grouping: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false },
];

const actionDialogs = {
    '': { 'message': "This action is not undoable." },
    'update': { 'message': "This action is not undoable." },
    'rerun': { 'message': "This action is not undoable." },
    'delete': { 'message': "This action is not undoable." },
    'share': { 'message': "You can use 'unshare' to undo this action." },
    'unshare': { 'message': "You can use 'share' to undo this action." },
    'publish': { 'message': "You can use 'unpublish' to undo this action." },
    'unpublish': { 'message': "You can use 'publish' to undo this action." },
    'export': { 'message': "Export metadata of the selected projects to a csv file." },
}

function SraDataTable(props) {
    const dispatch = useDispatch();
    const user = useSelector(state => state.user);
    const errors = useSelector(state => state.errors);

    const [tableData, setTableData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedData, setSelectedData] = useState([]);
    const [openDialog, setOpenDialog] = useState(false);
    const [action, setAction] = useState('');
    const [openUserSelector, setOpenUserSelector] = useState(false);
    const [userlist, setUserlist] = useState([]);

    useEffect(() => {
        if (props.tableType === 'admin' && user.profile.type !== "admin") {
            props.history.push("/home");
        } else {
            if (props.tableType === 'admin') {
            }
            getProjects();
        }
    }, [props, user]);// eslint-disable-line react-hooks/exhaustive-deps

    const reloadProjects = () => {
        updateSelectedData([]);
        getProjects();
    }

    const getProjects = () => {
        let url = "/auth-api/user/project/sradata";
        if (props.tableType === 'admin') {
            url = "/auth-api/admin/project/sradata";
        }
        setIsLoading(true);
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
                    rObj['public'] = obj.public;
                    rObj['created'] = obj.created;
                    rObj['updated'] = obj.updated;
                    rObj['desc'] = obj.desc;
                    rObj['sharedto'] = obj.sharedto;
                    rObj['code'] = obj.code;

                    if(obj.sharedto && obj.sharedto.length > 0) {
                        rObj['shared'] = true;
                    } else {
                        rObj['shared'] = false;
                    }

                    return rObj;
                });
                setIsLoading(false);
                setTableData(projects);
            })
            .catch(err => {
                setIsLoading(false);
                alert(err);
            });
    }

    const updateProj = (proj, oldProj) => {
        const actionTitle = startCase(action) + " project '" + oldProj.name + "'";
        let err = '';
        if (!proj.name || proj.name.trim() === '') {
            err += "Project name is required.\n";
        }
        if (err === '') {
            if (props.tableType === 'admin') {
                dispatch(updateProjectAdmin(proj));
            } else {
                dispatch(updateProject(proj));
            }
            setTimeout(() => afterActionSubmit(actionTitle, proj.code), 500);
        } else {
            notify("error", actionTitle + " failed! " + err);
        }
    }

    const afterActionSubmit = (action, code) => {
        if (errors && errors[code]) {
            notify("error", action + " failed! " + errors[code]);
        } else {
            notify("success", action + " successfully!");
        }
    }

    const updateSelectedData = (rows) => {
        setSelectedData(rows);
    }

    const handleAction = (action) => {
        if (selectedData.length === 0) {
            return;
        }
        setOpenDialog(true);
        setAction(action);
    }

    const handleConfirmClose = () => {
        setOpenDialog(false);
    }

    const handleConfirmYes = async () => {
        setOpenDialog(false);

        //get user selector options
        if (action === 'share' || action === 'unshare') {
            setOpenUserSelector(true);
        } else if (action === 'export') {
            //do exporting
        } else {
            dispatch(cleanupMessages());
            const promises = selectedData.map(proj => {
                return proccessProject(proj);
            });
            Promise.all(promises).then((results) => {
                reloadProjects();
            });
        }
    }

    const proccessProject = (proj) => {
        if (action === 'delete') {
            proj.status = 'delete';
        }
        else if (action === 'rerun') {
            proj.status = 'rerun';
        }
        else if (action === 'publish') {
            proj.public = true;
        }
        else if (action === 'unpublish') {
            proj.public = false;
        }

        updateProj(proj, proj);

        return true;
    }

    const handleUserSelectorChange = (selectedUsers) => {
        setUserlist(selectedUsers.map(user => {
            return (user.value)
        }));
    }

    const handleUserSelectorYes = async () => {
        setOpenUserSelector(false);

        dispatch(cleanupMessages());

        const promises = selectedData.map(proj => {
            return processShareUnshareProject(proj);
        });

        Promise.all(promises).then((results) => {
            reloadProjects();
        });
    }

    const processShareUnshareProject = (proj) => {
        if (action === 'share') {
            let sharedto = proj.sharedto;
            userlist.map(user => {
                if (proj.owner === user) {
                }
                else if (!sharedto.includes(user)) {
                    sharedto.push(user);
                }
                return 1;
            });

            proj.sharedto = sharedto;
        }
        else if (action === 'unshare') {
            let sharedto = proj.sharedto;
            userlist.map(user => {
                var index = sharedto.indexOf(user);
                sharedto.splice(index, 1);
                return 1;
            });

            proj.sharedto = sharedto;
        }

        updateProj(proj, proj);

        return true;
    }

    const handleUserSelectorClose = () => {
        setOpenUserSelector(false);
    }

    return (
        <>
            <ToastContainer />
            <ConfirmDialog isOpen={openDialog} action={action} title={"Are you sure to " + action + " the selected projects?"}
                message={actionDialogs[action].message} handleClickYes={handleConfirmYes} handleClickClose={handleConfirmClose} />
            {openUserSelector &&
                <UserSelector type={props.tableType} isOpen={openUserSelector} action={action} onChange={handleUserSelectorChange}
                    handleClickYes={handleUserSelectorYes} handleClickClose={handleUserSelectorClose} />
            }

            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    isLoading={isLoading}
                    columns={columns}
                    data={tableData}
                    title={props.title}
                    icons={tableIcons}
                    options={{
                        grouping: false,
                        selection: true,
                        pageSize: 10,
                        pageSizeOptions: [10, 20, 50, 100],
                        addRowPosition: 'first',
                        columnsButton: true,
                        actionsColumnIndex: 9,
                        emptyRowsWhenPaging: false,
                        showTitle: true,
                    }}
                    //onRowClick={((evt, selectedRow) => {})}
                    onSelectionChange={(rows) => updateSelectedData(rows)}
                    detailPanel={[
                        {
                            tooltip: 'More info',
                            render: rowdata => {
                                return (
                                    <div style={{ margin: '15px', textAlign: 'left', }} >
                                        {(props.tableType === 'admin' || rowdata.owner === user.profile.email) &&
                                            <>
                                                <br></br>
                                                <b>Shared To:</b> {rowdata.sharedto.join(', ')}
                                            </>
                                        }
                                    </div>
                                )
                            }
                        },
                    ]}

                    components={{
                        Toolbar: props => (
                            <div>
                                <MTableToolbar {...props} />
                                <div style={{ padding: '10px 10px' }} >
                                    <Tooltip title="Delete selected projects" aria-label="delete">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="delete">
                                            <DeleteIcon onClick={() => handleAction('delete')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Share selected projects" aria-label="share">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="share">
                                            <PersonAddIcon onClick={() => handleAction('share')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Unshare selected projects" aria-label="unshare">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="unshare">
                                            <PersonAddDisabledIcon onClick={() => handleAction('unshare')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Publish selected projects" aria-label="publish">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="publish">
                                            <LockOpenIcon onClick={() => handleAction('publish')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Unpublish selected projects" aria-label="unpublish">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="unpublish">
                                            <LockIcon onClick={() => handleAction('unpublish')} />
                                        </Fab>
                                    </Tooltip>
                                </div>
                            </div>
                        ),
                    }}
                    actions={[
                        {
                            icon: () => <RefreshIcon />,
                            tooltip: 'Refresh Data',
                            isFreeAction: true,
                            onClick: () => getProjects(),
                        }
                    ]}
                />

            </MuiThemeProvider>
        </>
    );
}

export default SraDataTable;