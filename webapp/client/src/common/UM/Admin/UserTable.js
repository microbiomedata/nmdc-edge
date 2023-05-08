import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addUser, updateUser, deleteUser } from "../../../redux/actions/adminActions";
import { Badge } from 'reactstrap';
import { ToastContainer } from 'react-toastify';
import { notify, getData } from "../../util";
import 'react-toastify/dist/ReactToastify.css';

import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, userStatusColors, userStatusNames, userTypeColors, userTypeNames } from '../../table';

import RefreshIcon from '@material-ui/icons/Refresh';

const columns = [
    { title: 'First Name', field: 'firstname', },
    { title: 'Last Name', field: 'lastname', },
    { title: 'Email', field: 'email', editable: 'onAdd', grouping: false },
    { title: 'Password', field: 'password', hidden: true, filtering: false, grouping: false },
    {
        title: 'Type', field: 'type', grouping: false,
        render: rowData => { return <Badge color={userTypeColors[rowData.type]}>{userTypeNames[rowData.type]}</Badge> },
        lookup: { 'admin': 'Admin', 'user': 'User' }, initialEditValue: 'user'
    },
    {
        title: 'Status', field: 'status', grouping: false,
        render: rowData => { return <Badge color={userStatusColors[rowData.status]}>{userStatusNames[rowData.status]}</Badge> },
        lookup: { 'inactive': 'Inactive', 'active': 'Active' }, initialEditValue: 'active'
    },
    { title: 'Created', field: 'created', type: 'datetime', editable: 'never', hidden: true, filtering: false, grouping: false },
    { title: 'Updated', field: 'updated', type: 'datetime', editable: 'never', filtering: false, grouping: false },
];

function UserTable(props) {
    const dispatch = useDispatch();
    const user = useSelector(state => state.user);
    const errors = useSelector(state => state.errors);

    const [tableData, setTableData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (user.profile.type !== "admin") {
            props.history.push("/home");
        } else {
            getUsers();
        }
    }, [props, user]);

    const getUsers = () => {
        let url = "/auth-api/admin/user/list";
        setIsLoading(true);
        getData(url)
            .then(data => {
                let users = data.map(obj => {
                    let rObj = {};
                    rObj['id'] = obj._id;
                    rObj['firstname'] = obj.firstname;
                    rObj['lastname'] = obj.lastname;
                    rObj['email'] = obj.email;
                    rObj['type'] = obj.type;
                    rObj['status'] = obj.status;
                    rObj['created'] = obj.created;
                    rObj['updated'] = obj.updated;
                    return rObj;
                });
                setTableData(users);
                setIsLoading(false);
            })
            .catch(err => {
                setIsLoading(false);
                alert(err);
            });
    }

    const myAddUser = (newUser) => {
        let err = '';
        if (!newUser.firstname || newUser.firstname.trim() === '') {
            err += "First Name is required.\n";
        }
        if (!newUser.lastname || newUser.lastname.trim() === '') {
            err += "Last Name is required.\n";
        }
        if (!newUser.password || newUser.password.trim() === '' || newUser.password.trim().length < 8) {
            err += "Password is required and must be at lease 8 characters in length.\n";
        }
        if (!newUser.email || !validateEmail(newUser.email)) {
            err += "Invalid email.\n";
        }

        if (err === '') {
            newUser.password2 = newUser.password;

            dispatch(addUser(newUser));
            setTimeout(() => afterActionSubmit('add new user ' + newUser.email), 500);

        } else {
            notify("error", "Failed to add new user " + newUser.email + ". " + err);

        }
    }

    const myUpdateUser = (newUser) => {
        let err = '';
        if (!newUser.firstname || newUser.firstname.trim() === '') {
            err += "First Name is required.\n";
        }
        if (!newUser.lastname || newUser.lastname.trim() === '') {
            err += "Last Name is required.\n";
        }
        if (newUser.password && (newUser.password.trim() === '' || newUser.password.trim().length < 8)) {
            err += "Password must be at lease 8 characters in length.\n";
        }
        if (newUser.password) {
            newUser.password2 = newUser.password;
        }

        if (err === '') {
            if (newUser.password) {
                newUser.password2 = newUser.password;
            }

            dispatch(updateUser(newUser));
            setTimeout(() => afterActionSubmit('update user ' + newUser.email), 500);

        } else {
            notify("error", "Failed to update user " + newUser.email + ". " + err);
        }
    }

    const myDeleteUser = (myuser) => {
        dispatch(deleteUser(myuser));
        setTimeout(() => afterActionSubmit('delete user ' + myuser.email), 500);

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
            getUsers();
        }
    }

    const validateEmail = (email) => {
        var re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(email);
    }

    return (
        <>
            <ToastContainer />
            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    isLoading={isLoading}
                    columns={columns}
                    data={tableData}
                    title={props.title}
                    icons={tableIcons}
                    //onRowClick={((evt, selectedRow) => {})}
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
                    editable={{
                        onRowAdd: newData =>
                            new Promise((resolve, reject) => {
                                setTimeout(() => {
                                    myAddUser(newData);
                                    resolve()
                                }, 1000)
                            }),
                        onRowUpdate: (newData, oldData) =>
                            new Promise((resolve, reject) => {
                                setTimeout(() => {
                                    myUpdateUser(newData);
                                    resolve()
                                }, 1000)
                            }),
                        onRowDelete: oldData =>
                            new Promise((resolve, reject) => {
                                setTimeout(() => {
                                    myDeleteUser(oldData);
                                    resolve()
                                }, 1000)
                            }),
                    }}
                    actions={[
                        {
                            icon: () => <RefreshIcon />,
                            tooltip: 'Refresh Data',
                            isFreeAction: true,
                            onClick: () => getUsers(),
                        }
                    ]}
                />
            </MuiThemeProvider>
        </>
    );
}

export default UserTable;