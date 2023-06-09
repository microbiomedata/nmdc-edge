const axios = require("axios");
const fs = require('fs');
const logger = require('./logger');
const Upload = require("../models/Upload");

async function getRealName(dir) {
    let name = dir;
    //check if input is a uploaded file
    let upload = await Upload.findOne({ 'code': dir });

    if (upload) {
        name = upload.name;
    }
    return name;
}


//append message to a log
const write2log = (log, msg) => {
    fs.appendFile(log, msg + "\n", function (err) {
        if(err) logger.error("Failed to write to " + log + ": " + err);
    });
};

//post data
const postData = (url, params, header) => {
    return new Promise(function (resolve, reject) {
        axios
            .post(url, params, header)
            .then(response => {
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                if (err.response) {
                    reject(err.response);
                } else {
                    reject(err);
                }
            });

    });
};

//get data
const getData = (url) => {
    return new Promise(function (resolve, reject) {
        axios
            .get(url)
            .then(response => {
                const data = response.data;
                resolve(data);
            })
            .catch(err => {
                if (err.response) {
                    reject(err.response);
                } else {
                    reject(err);
                }
            });

    });
};

module.exports = { getRealName, write2log, postData, getData };