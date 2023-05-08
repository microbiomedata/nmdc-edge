import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { updateFileAdmin } from "../../../redux/actions/adminActions";
import { updateFile, cleanupMessages } from "../../../redux/actions/userActions";
import UserSelector from './UserSelector';
import { ConfirmDialog } from '../../Dialogs';
import startCase from 'lodash.startcase';

import { ToastContainer } from 'react-toastify';
import { notify, getData, formatFileSize } from "../../util";
import 'react-toastify/dist/ReactToastify.css';

import MaterialTable, { MTableToolbar } from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme } from '../../table';

import Fab from '@material-ui/core/Fab';
import DeleteIcon from '@material-ui/icons/Delete';
import RefreshIcon from '@material-ui/icons/Refresh';
import PersonAddIcon from '@material-ui/icons/PersonAdd';
import PersonAddDisabledIcon from '@material-ui/icons/PersonAddDisabled';
import LockIcon from '@material-ui/icons/Lock';
import LockOpenIcon from '@material-ui/icons/LockOpen';
import Tooltip from '@material-ui/core/Tooltip';

const columns = [
    { title: 'File Name', field: 'name', filterPlaceholder: 'File filter', tooltip: 'File name', grouping: false },
    { title: 'Description', field: 'desc', hidden: true, grouping: false },
    { title: 'Type', field: 'type', editable: 'never' },
    { title: 'Size', field: 'size', editable: 'never', grouping: false },
    { title: 'Owner', field: 'owner', editable: 'never', tooltip: 'File owner', hidden: true },
    { title: 'Public', field: 'public', lookup: { true: 'Yes', false: 'No' } },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', filtering: false, grouping: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false },
];

const actionDialogs = {
    '': { 'message': "This action is not undoable." },
    'update': { 'message': "This action is not undoable." },
    'delete': { 'message': "This action is not undoable." },
    'share': { 'message': "You can use 'unshare' to undo this action." },
    'unshare': { 'message': "You can use 'share' to undo this action." },
    'publish': { 'message': "You can use 'unpublish' to undo this action." },
    'unpublish': { 'message': "You can use 'publish' to undo this action." },
}

function FileTable(props) {
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
            getFiles();
        }
    }, [props, user]);// eslint-disable-line react-hooks/exhaustive-deps

    const reloadFiles = () => {
        setSelectedData([]);
        getFiles();
    }

    const getFiles = () => {
        let url = "/auth-api/user/upload/list";
        if (props.tableType === 'admin') {
            url = "/auth-api/admin/upload/list";
        }
        setIsLoading(true);

        getData(url)
            .then(data => {
                let files = data.map(obj => {
                    //console.log(obj)
                    let rObj = {};
                    rObj['id'] = obj._id;
                    rObj['name'] = obj.name;
                    rObj['owner'] = obj.owner;
                    rObj['type'] = obj.type;
                    rObj['size'] = formatFileSize(obj.size);
                    rObj['public'] = obj.public;
                    rObj['created'] = obj.created;
                    rObj['updated'] = obj.updated;
                    rObj['desc'] = obj.desc;
                    rObj['sharedto'] = obj.sharedto;
                    rObj['code'] = obj.code;

                    return rObj;
                });
                setIsLoading(false);
                setTableData(files);
            })
            .catch(err => {
                setIsLoading(false);
                alert(err);
            });
    }

    const myUpdateFile = (file, oldFile) => {
        const actionTitle = startCase(action) + " file '" + oldFile.name + "'";
        let err = '';
        if (!file.name || file.name.trim() === '') {
            err += "File name is required.\n";
        }
        if (err === '') {
            if (props.tableType === 'admin') {
                dispatch(updateFileAdmin(file));
            } else {
                dispatch(updateFile(file));
            }
            setTimeout(() => afterActionSubmit(actionTitle, file.code), 500);
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

    const handleAction = (action) => {
        if (selectedData.length === 0) {
            return;
        }
        setOpenDialog(true);
        setAction(action);
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
            const promises = selectedData.map(file => {
                return proccessFile(file);
            });
            Promise.all(promises).then((results) => {
                reloadFiles();
            });
        }
    }

    const proccessFile = (file) => {
        if (action === 'delete') {
            file.status = 'delete';
        } else if (action === 'publish') {
            file.public = true;
        } else if (action === 'unpublish') {
            file.public = false;
        }

        myUpdateFile(file, file);

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

        const promises = selectedData.map(file => {
            return processShareUnshareFile(file);
        });

        Promise.all(promises).then((results) => {
            reloadFiles();
        });
    }

    const processShareUnshareFile = (file) => {
        if (action === 'share') {
            let sharedto = file.sharedto;
            userlist.map(user => {
                if (file.owner === user) {
                }
                else if (!sharedto.includes(user)) {
                    sharedto.push(user);
                }
                return 1;
            });

            file.sharedto = sharedto;
        }
        else if (action === 'unshare') {
            let sharedto = file.sharedto;
            userlist.map(user => {
                var index = sharedto.indexOf(user);
                sharedto.splice(index, 1);
                return 1;
            });

            file.sharedto = sharedto;
        }

        myUpdateFile(file, file);

        return true;
    }
    return (
        <>
            <ToastContainer />
            <ConfirmDialog isOpen={openDialog} action={action} title={"Are you sure to " + action + " the selected files?"}
                message={actionDialogs[action].message} handleClickYes={handleConfirmYes} handleClickClose={() => setOpenDialog(false)} />
            {openUserSelector &&
                <UserSelector type={props.tableType} isOpen={openUserSelector} action={action} onChange={handleUserSelectorChange}
                    handleClickYes={handleUserSelectorYes} handleClickClose={() => setOpenUserSelector(false)} />
            }

            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    isLoading={isLoading}
                    columns={columns}
                    data={tableData}
                    title={props.title}
                    icons={tableIcons}
                    options={{
                        grouping: true,
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
                    onSelectionChange={(rows) => setSelectedData(rows)}
                    detailPanel={[
                        {
                            tooltip: 'More info',
                            render: rowdata => {
                                return (
                                    <div style={{ margin: '15px', textAlign: 'left', }} >
                                        <b>Description:</b> {rowdata.desc}
                                        {(props.tableType === 'admin' || rowdata.owner === user.profile.email) &&
                                            <>
                                                <br></br>
                                                <b>Shared To:</b> {rowdata.sharedto.join(', ')}
                                            </>
                                        }
                                    </div>
                                )
                            }
                        }
                    ]}
                    editable={{
                        onRowUpdate: (newData, oldData) =>
                            new Promise((resolve, reject) => {
                                setAction("update");
                                myUpdateFile(newData, oldData);

                                setTimeout(() => { reloadFiles(); }, 1000);
                                resolve();
                            }),
                    }}

                    components={{
                        Toolbar: props => (
                            <div>
                                <MTableToolbar {...props} />
                                <div style={{ padding: '10px 10px' }} >
                                    <Tooltip title="Delete selected files" aria-label="delete">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="delete">
                                            <DeleteIcon onClick={() => handleAction('delete')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Share selected files" aria-label="share">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="share">
                                            <PersonAddIcon onClick={() => handleAction('share')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Unshare selected files" aria-label="unshare">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="unshare">
                                            <PersonAddDisabledIcon onClick={() => handleAction('unshare')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Publish selected files" aria-label="publish">
                                        <Fab color="primary" size='small' style={{ marginRight: 10 }} aria-label="publish">
                                            <LockOpenIcon onClick={() => handleAction('publish')} />
                                        </Fab>
                                    </Tooltip>
                                    <Tooltip title="Unpublish selected files" aria-label="unpublish">
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
                            onClick: () => getFiles(),
                        }
                    ]}
                />

            </MuiThemeProvider>
        </>
    );
}

export default FileTable;