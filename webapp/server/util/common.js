const axios = require("axios");
const fs = require('fs');
const logger = require('./logger');
const Upload = require("../models/Upload");
const Project = require("../models/Project");
const config = require("../config");

async function getRealName(dir) {
    let name = dir;
    //check if input is a uploaded file
    let upload = await Upload.findOne({ 'code': dir });

    if (upload) {
        name = upload.name;
    }
    return name;
}

async function getRunningProjects(proj) {
    const projects = await Project.find({ 'owner': proj.owner, 'status': { $in: ['processing', 'submitted', 'running'] } });
    return projects.length;
}


//append message to a log
const write2log = (log, msg) => {
    fs.appendFile(log, msg + "\n", function (err) {
        if (err) logger.error("Failed to write to " + log + ": " + err);
    });
};

//post data
const postData = (url, params, header) => {
    return new Promise(function (resolve, reject) {
        axios
            .post(url, params, header)
            .then(response => {
                //console.log("post response: ", response);
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                //console.log("post err: ", err);
                if (err.response) {
                    reject(err.response);
                } else {
                    reject(err);
                }
            });

    });
};

//get data
const getData = (url, header) => {
    return new Promise(function (resolve, reject) {
        axios
            .get(url, header)
            .then(response => {
                //console.log("get request response: ", response);
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                //console.log("get request err: ", err);
                if (err.response) {
                    reject(err.response);
                } else {
                    reject(err);
                }
            });

    });
};

//delete data
const deleteData = (url, header) => {
    return new Promise(function (resolve, reject) {
        axios
            .delete(url, header)
            .then(response => {
                //console.log("delete request response: ", response);
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                //console.log("delete request err: ", err);
                if (err.response) {
                    reject(err.response);
                } else {
                    reject(err);
                }
            });

    });
};

// nmdc api
const nmdcAPI = axios.create({
    baseURL: config.PROJECTS.NMDC_SERVER_URL,
});

module.exports = { getRealName, getRunningProjects, write2log, postData, getData, deleteData };