const fs = require('fs');
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const config= require("../config");

const { getResult, getRunStats, getConf } = require("../util/pipeline");

const projectResult = function (project) {
    return getResult(project);
}

const runStats = function (project) {
    return getRunStats(project);
}

const conf = function (project) {
    return getConf(project);
}

const encodePassword = function (password) {
    return new Promise((resolve, reject) => {
        // Hash password before saving in database
        bcrypt.genSalt(10, (err, salt) => {
            bcrypt.hash(password, salt, (err, hash) => {
                if (err) {
                    logger.error("Failed to encode password: " + err);
                    return reject(err);
                }
                resolve(hash);
            });
        });
    });
}

const signToken = function (payload) {
    return new Promise((resolve, reject) => {
        // Sign token
        jwt.sign(
            payload,
            config.AUTH.JWT_SECRET,
            {
                expiresIn: 31556926 // 1 year in seconds
            },
            (err, token) => {
                if (err) {
                    logger.error("Failed to generate a jwt token: " + err);
                    return reject(err);
                }
                resolve(token);
            }
        );
    });
}

//files
//Get file data for file browser
//get all files in a directory
const getAllFiles = function (dirPath, arrayOfFiles, extentions, displayPath, apiPath, fileRelPath, endsWith) {
    files = fs.readdirSync(dirPath)

    arrayOfFiles = arrayOfFiles || []

    files.forEach(function (file) {
        try {
            if (fs.statSync(dirPath + "/" + file).isDirectory()) {
                arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles, extentions, displayPath + "/" + file, apiPath + "/" + file, fileRelPath + "/" + file, endsWith)
            } else {
                let pass = false;
                if (extentions && extentions.length > 0) {
                    for (var i = 0; i < extentions.length; i++) {
                        if (file === extentions[i]) {
                            pass = true;
                        } else if (file.endsWith("." + extentions[i])) {
                            pass = true;
                        } else if(endsWith && file.endsWith(extentions[i])) {
                            pass = true;
                        } 
                    }
                } else {
                    //get all files
                    pass = true;
                }
                if (pass) {
                    const file_path = path.join(dirPath, "/", file);
                    const file_rel_path = path.join(fileRelPath, "/", file);
                    var stats = fs.statSync(file_path);
                    const display_path = path.join(displayPath, "/", file);
                    const api_path = path.join(apiPath, "/", file);
                    arrayOfFiles.push({ key: display_path, name: file, path: api_path, url: api_path, filePath: file_rel_path, size: stats.size, modified: Number(new Date(stats.mtime)) });
                }
            }
        } catch (err) {

        }
    })

    return arrayOfFiles
}

const sortObject = function (unordered, sortArrays = false) {
    if (!unordered || typeof unordered !== 'object') {
        return unordered;
    }

    if (Array.isArray(unordered)) {
        const newArr = unordered.map((item) => sortObject(item, sortArrays));
        if (sortArrays) {
            newArr.sort();
        }
        return newArr;
    }

    const ordered = {};
    Object.keys(unordered)
        .sort()
        .forEach((key) => {
            ordered[key] = sortObject(unordered[key], sortArrays);
        });
    return ordered;
}

module.exports = { projectResult, runStats, conf, getAllFiles, encodePassword, signToken, sortObject };