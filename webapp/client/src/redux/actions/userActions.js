import { setAuthToken, sendMail, postData } from "../../common/util";
import jwt_decode from "jwt-decode";
import {
    ADD_ERRORS,
    CLEAN_ERRORS,
    ADD_MESSAGES,
    CLEAN_MESSAGES,
    SET_CURRENT_USER,
    SET_NEW_USER,
    USER_LOADING,
    SUBMIT_FORM,
    SIDEBAR_SET
} from "./types";

// Register User
export const register = (userData) => dispatch => {
    dispatch({
        type: SUBMIT_FORM,
        payload: true
    });
    postData("/api/user/register", userData)
        .then(data => {
            const { user, mail_token } = data;
            // Set new user
            if (!userData.byAdmin) {
                dispatch(setNewUser(user));
            }
            let msg = "Congratulations! Your account has been created successfully.";
            if (process.env.REACT_APP_EMAIL_NOTIFICATION && process.env.REACT_APP_EMAIL_NOTIFICATION.toLowerCase() === 'true') {
                //sendmail
                const message = {
                    subject: process.env.REACT_APP_REGISTER_SUBJECT,
                    text: process.env.REACT_APP_REGISTER_MSG + "?email=" + user.email + "&token=" + encodeURI(user.password).replace(/\./g, '%2E')
                }
                sendMail(user.email, message, mail_token).then(data => {
                    msg = "Congratulations! Your account has been created successfully. Please check your email to activate your account.";
                    dispatch({
                        type: ADD_MESSAGES,
                        payload: { "register": msg }
                    });
                }).catch((error) => {
                    dispatch({
                        type: ADD_ERRORS,
                        payload: { "register": error }
                    });
                });
            } else {
                dispatch({
                    type: ADD_MESSAGES,
                    payload: { "register": msg }
                });
            }
            dispatch({
                type: SUBMIT_FORM,
                payload: false
            });
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "register": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
            dispatch({
                type: SUBMIT_FORM,
                payload: false
            });
        });
};

// Activate 
export const activate = (userData) => dispatch => {
    postData("/api/user/activate", userData)
        .then(data => {
            dispatch({
                type: ADD_MESSAGES,
                payload: { "activate": "Congratulations! Your account has been activated successfully." }
            });
            const { user } = data;
            dispatch(setNewUser(user));

        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "activate": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};
// Activate 
export const getActivationLink = (userData) => dispatch => {
    postData("/api/user/getActivationLink", userData)
        .then(data => {
            const { user, mail_token } = data;
            // Set new user
            dispatch(setNewUser(user));

            if (process.env.REACT_APP_EMAIL_NOTIFICATION && process.env.REACT_APP_EMAIL_NOTIFICATION.toLowerCase() === 'true') {
                //sendmail
                const message = {
                    subject: process.env.REACT_APP_REGISTER_SUBJECT,
                    text: process.env.REACT_APP_REGISTER_MSG + "?email=" + user.email + "&token=" + encodeURI(user.password).replace(/\./g, '%2E')
                }
                sendMail(user.email, message, mail_token).then(data => {
                    dispatch({
                        type: ADD_MESSAGES,
                        payload: { "getActivationLink": "Please check your email to activate your account." }
                    });
                }).catch((error) => {
                    dispatch({
                        type: ADD_ERRORS,
                        payload: { "activate": error }
                    });
                });
            }
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "activate": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// resetpassword 
export const resetpassword = (userData) => dispatch => {
    postData("/api/user/resetpassword", userData)
        .then(data => {
            dispatch({
                type: ADD_MESSAGES,
                payload: { "resetpassword": "Congratulations! Your password has been updated successfully." }
            });
            const { user } = data.data;
            dispatch(setNewUser(user));

        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "resetpassword": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};
// resetpassword 
export const getResetpasswordLink = (userData) => dispatch => {
    postData("/api/user/getResetpasswordLink", userData)
        .then(data => {
            const { user, mail_token } = data;
            // Set new user
            dispatch(setNewUser(user));

            if (process.env.REACT_APP_EMAIL_NOTIFICATION && process.env.REACT_APP_EMAIL_NOTIFICATION.toLowerCase() === 'true') {
                //sendmail
                const message = {
                    subject: process.env.REACT_APP_RESETPASSWD_SUBJECT,
                    text: process.env.REACT_APP_RESETPASSWD_MSG + "?email=" + user.email + "&token=" + encodeURI(user.password).replace(/\./g, '%2E')
                }

                sendMail(user.email, message, mail_token).then(data => {
                    dispatch({
                        type: ADD_MESSAGES,
                        payload: { "getResetpasswordLink": "Please check your email to reset your password." }
                    });
                }).catch((error) => {
                    dispatch({
                        type: ADD_ERRORS,
                        payload: { "resetpasswordLink": error }
                    });
                });
            }
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "resetpasswordLink": err }
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
export const update = userData => dispatch => {
    postData("/auth-api/user/update", userData)
        .then(data => {
            if (!userData.byAdmin) {
                // Save to localStorage
                // Set token to localStorage
                const { token } = data;
                localStorage.setItem("jwtToken", token);
                //console.log("set local store: " + localStorage.jwtToken);
                // Set token to Auth header
                setAuthToken(token);
                // Decode token to get user data
                const decoded = jwt_decode(token);
                // Set current user
                dispatch(setCurrentUser(decoded));
                dispatch({
                    type: ADD_MESSAGES,
                    key: "update",
                    payload: "Your account has been updated successfully." 
                });
            }
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "update": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// Login - get user token
export const login = userData => dispatch => {
    postData("/api/user/login", userData)
        .then(data => {
            // Save to localStorage
            // Set token to localStorage
            const { token } = data;
            localStorage.setItem("jwtToken", token);
            // Set token to Auth header
            setAuthToken(token);
            // Decode token to get user data
            const decoded = jwt_decode(token);
            // Set current user
            dispatch(setCurrentUser(decoded));
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "login": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
        });
};

// Social login
export const socialLogin = (userData) => dispatch => {
    dispatch({
        type: SUBMIT_FORM,
        payload: true
    });
    postData("/api/user/sociallogin", userData)
        .then(data => {
            // Save to localStorage
            // Set token to localStorage
            const { token } = data;
            if (token) {
                localStorage.setItem("jwtToken", token);
                // Set token to Auth header
                setAuthToken(token);
                // Decode token to get user data
                const decoded = jwt_decode(token);
                // Set current user
                dispatch(setCurrentUser(decoded));
            } else {
                const { user, mail_token } = data;
                // Set new user
                dispatch(setNewUser(user));
                //sendmail
                const message = {
                    subject: process.env.REACT_APP_REGISTER_SUBJECT,
                    text: process.env.REACT_APP_REGISTER_MSG + "?email=" + user.email + "&token=" + encodeURI(user.password).replace(/\./g, '%2E')
                }
                sendMail(user.email, message, mail_token).then(data => {
                    let msg = "Please check your email (" + user.email + ") to activate your account.";
                    dispatch({
                        type: ADD_MESSAGES,
                        payload: { "sociallogin": msg }
                    });
                }).catch((error) => {
                    dispatch({
                        type: ADD_ERRORS,
                        payload: { "rsociallogin": error }
                    });
                });

            }
            dispatch({
                type: SUBMIT_FORM,
                payload: false
            });
        })
        .catch(err => {
            if (typeof err === 'string') {
                dispatch({
                    type: ADD_ERRORS,
                    payload: { "sociallogin": err }
                });
            } else {
                dispatch({
                    type: ADD_ERRORS,
                    payload: err
                });
            }
            dispatch({
                type: SUBMIT_FORM,
                payload: false
            });
        });
};

// Set new user
export const setNewUser = decoded => {
    return {
        type: SET_NEW_USER,
        payload: decoded
    };
};

// Set logged in user
export const setCurrentUser = decoded => {
    return {
        type: SET_CURRENT_USER,
        payload: decoded
    };
};

// User loading
export const setUserLoading = () => {
    return {
        type: USER_LOADING
    };
};

// Log user out
export const logout = history => dispatch => {
    // Remove token from local storage
    localStorage.removeItem("jwtToken");
    // Remove auth header for future requests
    setAuthToken(false);
    // Set current user to empty object {} which will set isAuthenticated to false
    dispatch(setCurrentUser({}));
};

// Log user out
export const logoutFacebook = () => dispatch => {
    window.FB.logout();
};

// Update project
export const updateProject = projData => dispatch => {
    postData("/auth-api/user/project/update", projData)
        .then(data => {
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
                })
            }
        });
};

//uploaded file
export const updateFile = fileData => dispatch => {
    postData("/auth-api/user/upload/update", fileData)
        .then(data => {
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

export const cleanupMessages = () => dispatch => {
    dispatch({
        type: CLEAN_ERRORS
    });
    dispatch({
        type: CLEAN_MESSAGES
    });
};

// Set sidebar
export const setSidebar = val => dispatch => {
    dispatch({
        type: SIDEBAR_SET,
        payload: val
    });
};