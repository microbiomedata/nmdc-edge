import { postData } from '../../common/util';
import {
    ADD_ERRORS,
} from "./types";

// Register User
export const addUser = (userData) => dispatch => {
    postData("/auth-api/admin/user/add", userData)
        .then(res => {
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "error": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// Update User
export const updateUser = userData => dispatch => {
    postData("/auth-api/admin/user/update", userData)
        .then(res => {
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "error": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// Update User
export const deleteUser = userData => dispatch => {
    postData("/auth-api/admin/user/delete", userData)
        .then(res => {
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "error": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// Update project
export const updateProjectAdmin = projData => dispatch => {
    postData("/auth-api/admin/project/update", projData)
        .then(res => {
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    key: projData.code,
                    payload: err
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    key: projData.code,
                    payload: err[projData.code]
                });
            }
        });
};

// Update upload file
export const updateFileAdmin = fileData => dispatch => {
    postData("/auth-api/admin/upload/update", fileData)
        .then(res => {
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    key: fileData.code,
                    payload: err
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    key: fileData.code,
                    payload: err[fileData.code]
                })
            }
        });
};