import axios from 'axios';
import { toast } from 'react-toastify';

//action notification
export const notify = (type, msg, timeout) => {
    if (!timeout) timeout = 2000;
    if (type === 'success') {
        toast.success(msg, {
            position: toast.POSITION.TOP_CENTER,
            autoClose: timeout
        });
    }
    if (type === 'error') {
        toast.error(msg, {
            position: toast.POSITION.TOP_CENTER,
            autoClose: false
        });
    }
};

//fetch data
export const postData = (url, params) => {
    return new Promise(function (resolve, reject) {
        axios
            .post(url, params)
            .then(response => {
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                if (err.response) {
                    reject(err.response.data);
                } else {
                    reject(err);
                }
            });

    });
};

//fetch data
export const getData = (url) => {
    return new Promise(function (resolve, reject) {
        axios
            .get(url)
            .then(response => {
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                if (err.response) {
                    reject(err.response.data);
                } else {
                    reject(err);
                }
            });

    });
};

//fetch file
export const fetchFile = (url) => {
    return new Promise(function (resolve, reject) {
        axios
            .get(url)
            .then(response => {
                const data = response.data;
                //console.log(data)
                resolve(data);
            })
            .catch(err => {
                if (err.response) {
                    reject(err.response.data);
                } else {
                    reject(err);
                }
            });

    });
};

//set token to API request header
export const setAuthToken = token => {
    if (token) {
        // Apply authorization token to every request if logged in
        axios.defaults.headers.common["Authorization"] = token;
    } else {
        // Delete auth header
        delete axios.defaults.headers.common["Authorization"];
    }
};

export const sendMail = (recipient, message, token) => {
    const data = {
        to: recipient,
        message: message,
        token: token
    };
    return postData("/api/user/sendmail", data);
};

//format file size
export const formatFileSize = (number) => {
    if (number < 1024) {
        return number + 'bytes';
    } else if (number >= 1024 && number < 1048576) {
        return (number / 1024).toFixed(1) + 'KB';
    } else if (number >= 1048576 && number < 1073741824) {
        return (number / 1048576).toFixed(1) + 'MB';
    } else if (number >= 1073741824) {
        return (number / 1073741824).toFixed(1) + 'GB';
    }
}

export const getFileExtension = (name) => {
    const parts = name.split('.');
    const len = parts.length;
    let ext = parts[len - 1];
    if (ext === 'gz' && len > 2) {
        ext = parts[len - 2] + ".gz";
    }
    return ext.toLowerCase();
}

export const popupWindow = (url, windowName, win, w, h) => {
    const y = win.top.outerHeight / 2 + win.top.screenY - (h / 2);
    const x = win.top.outerWidth / 2 + win.top.screenX - (w / 2);
    return win.open(url, windowName, `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${y}, left=${x}`);
}


