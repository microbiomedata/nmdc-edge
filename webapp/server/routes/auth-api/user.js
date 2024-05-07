const express = require("express");
const path = require("path");
const router = express.Router();
const bcrypt = require("bcryptjs");
const randomize = require('randomatic');
const fs = require('fs');
const Validator = require("validator");
const dbsanitize = require('mongo-sanitize');
const moment = require('moment');
const jsonQuery = require('json-query');
const config = require("../../config");
const { workflowlist } = require("../../config/workflow");

// Load input validation
const validateUpdateInput = require("../../validation/user/update");
const validateAddprojectInput = require("../../validation/user/addproject");
const validateUpdateprojectInput = require("../../validation/user/updateproject");
const validateAdduploadInput = require("../../validation/user/addupload");
const isEmpty = require("is-empty");

// Load User model
const User = require("../../models/User");
const Project = require("../../models/Project");
const Upload = require("../../models/Upload");

const common = require("../common");
const logger = require('../../util/logger');

const sysError = "API server error";

// @route GET auth-api/user/info
// @access Private
router.get("/info", (req, res) => {
    logger.debug("/auth-api/user/info: " + req.user.email);
    if (process.env.SYSTEM_MESSAGE) {
        return res.send({
            info: {
                allowNewRuns: false,
                message: process.env.SYSTEM_MESSAGE,
            },
            message: 'Action successful',
            success: true,
        });
    } else {
        return res.send({
            info: {
                allowNewRuns: true,
            },
            message: 'Action successful',
            success: true,
        });
    }
});
// @route POST api/user/update
// @desc get user account 
// @access Private
router.post("/update", (req, res) => {
    logger.debug("/auth-api/user/update: " + req.user.email);
    // Form validation
    const { errors, isValid } = validateUpdateInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }
    let promise = new Promise(function (resolve, reject) {
        if (!isEmpty(req.body.password)) {
            // Hash password before saving in database
            bcrypt.genSalt(10, (err, salt) => {
                bcrypt.hash(req.body.password, salt, (err, hash) => {
                    if (err) reject(new Error(err));
                    resolve(hash);
                });
            });
        } else {
            resolve(null);
        }
    });

    promise.then(function (hashPassword) {
        User.findOne({ email: dbsanitize(req.user.email) }).then(user => {
            if (!user) {
                logger.debug("User not found: " + req.user.email);
                return res.status(400).json("User not found.");
            }

            //change code
            user.code = randomize("0", 6);
            user.firstname = req.body.firstname;
            user.lastname = req.body.lastname;
            if (!isEmpty(req.body.type)) {
                user.type = req.body.type;
            }
            if (!isEmpty(req.body.status)) {
                user.status = req.body.status;
            }
            if (!isEmpty(req.body.mailto)) {
                user.mailto = req.body.mailto;
            }
            if (!isEmpty(req.body.notification)) {
                user.notification = req.body.notification;
            }

            user.updated = Date.now();
            if (hashPassword) {
                user.password = hashPassword;
            }
            user.save().then(user => {
                // Create JWT Payload
                const payload = {
                    id: user.id,
                    firstname: user.firstname,
                    lastname: user.lastname,
                    email: user.email,
                    mailto: user.mailto,
                    notification: user.notification,
                    type: user.type,
                    status: user.status,
                    code: user.code
                };
                // Sign token
                common.signToken(payload).then(token => {
                    return res.json({
                        success: true,
                        token: "Bearer " + token
                    });
                }).catch(err => {
                    logger.error("Update: Failed to generate a jwt token: " + err);
                    return res.status(500).json(sysError);
                });
            }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
        }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
    }).catch(function (err) {
        logger.error(err);
        return res.status(500).json(err);
    });
});

// @route POST auth-api/user/list
// @access Private
//for share/unshare
router.get("/list", (req, res) => {
    logger.debug("/auth-api/user/list: " + req.user.email);
    User.find({ 'status': 'active' }, { firstname: 1, lastname: 1, email: 1 }).sort([['firstname', 1], ['lastname', 1]]).then(function (users) {
        return res.send(users);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });

});

// @route GET auth-api/user/project/alllist
// @access Private
//all projects the an user can access to
router.get("/project/alllist", (req, res) => {
    logger.debug("/auth-api/user/project/alllist: " + req.user.email);
    //find all project owned by user and shared to user or public
    Project.find({ 'status': { $ne: 'delete' }, $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }, { 'public': true }] }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/project/list
// @access Private
//projects owned by an user
router.get("/project/list", (req, res) => {
    logger.debug("/auth-api/user/project/list: " + req.user.email);
    //find all project owned by user 
    Project.find({ 'status': { $ne: 'delete' }, 'owner': dbsanitize(req.user.email) }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/project/list
// @access Private
//projects owned by an user
router.get("/project/sradata", (req, res) => {
    logger.debug("/auth-api/user/project/sradata: " + req.user.email);
    //find all project owned by user 
    Project.find({ 'status': { $ne: 'delete' }, 'type': 'Retrieve SRA Data', 'owner': dbsanitize(req.user.email) }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/project/queue
// @access Private
router.get("/project/queue", (req, res) => {
    logger.debug("/auth-api/user/project/queue: " + JSON.stringify(req.body));
    //get all projects with status in ('in queue', 'running', 'submitted')
    Project.find({ 'status': { $in: ['in queue', 'running', 'processing', 'submitted'] } }, { name: 1, owner: 1, type: 1, status: 1, created: 1, updated: 1 }).sort([['created', 1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/project/add
// @desc Add new project
// @access Private
router.post("/project/add", (req, res) => {
    logger.debug("/auth-api/user/project/add: " + JSON.stringify(req.body));
    let conf = req.body;
    if (typeof conf.project === 'string') {
        conf.project = JSON.parse(conf.project);
    }
    if (typeof conf.inputs === 'string') {
        conf.inputs = JSON.parse(conf.inputs);
    }
    if (typeof conf.params === 'string') {
        conf.params = JSON.parse(conf.params);
    }
    if (typeof conf.workflow === 'string') {
        conf.workflow = JSON.parse(conf.workflow);
    }
    if (typeof conf.inputDisplay === 'string') {
        conf.inputDisplay = JSON.parse(conf.inputDisplay);
    }
    if (typeof conf.workflows === 'string') {
        conf.workflows = JSON.parse(conf.workflows);
    }
    // Form validation
    const { errors, isValid } = validateAddprojectInput(conf);
    // Check validation
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }

    let code = randomize('Aa0', 16);
    let proj_home = path.join(config.PROJECTS.BASE_DIR, code);
    while (fs.existsSync(proj_home)) {
        code = randomize('Aa0', 16);
        proj_home = path.join(config.PROJECTS.BASE_DIR, code);
    }

    //sanitize input
    const proj_name = Validator.whitelist(Validator.trim(conf.project.name), '^0-9a-zA-Z\,\-\_\^\@\=\:\\\.\/\+ \'\"');
    const proj_desc = conf.project.desc;

    let promise = new Promise(function (resolve, reject) {
        fs.mkdirSync(proj_home);
        delete conf.project;
        //get params from conf_file if use a conf file
        if (conf.params) {
            let conf_file = conf.params.conf_file;
            if (conf_file) {
                logger.debug(conf_file)
                if (fs.existsSync(conf_file)) {
                    let rawdata = fs.readFileSync(conf_file);
                    result = JSON.parse(rawdata);
                    conf.params = result.params;
                } else {
                    reject("The config file you selected does not exist.");
                }
            }
        }
        let data = JSON.stringify(conf);
        fs.writeFileSync(proj_home + '/conf.json', data);

        //if it's batch submission, save uploaded excel sheet to project home
        if (conf.pipeline.endsWith('/batch')) {
            //save uploaded file
            const file = req.files.file;
            const mvTo = proj_home + "/" + file.name;
            file.mv(`${mvTo}`, err => {
                if (err) {
                    reject(sysError);
                }
                logger.debug("upload to:" + `${mvTo}`);
            })
        }
        resolve(proj_home);
    });

    promise.then(function (proj_dir) {
        const newProject = new Project({
            name: proj_name,
            desc: proj_desc,
            type: conf.pipeline,
            owner: req.user.email,
            code: code
        });
        newProject
            .save()
            .then(project => {
                return res.json({ project: project });
            })
            .catch(err => {
                //clean up project 
                //fs.rmSync(proj_home, { recursive: true });
                logger.error(err);
                return res.status(500).json(sysError);
            });
    }).catch(function (err) {
        //clean up project 
        //fs.rmSync(proj_home, { recursive: true });
        logger.error(err); return res.status(400).json(sysError);
    });
});

// @route POST auth-api/user/project/update
// @desc update project 
// @access Private
router.post("/project/update", (req, res) => {
    logger.debug("/auth-api/user/project/update: " + JSON.stringify(req.body));
    //assume project code is provided
    let { errors, isValid } = validateUpdateprojectInput(req.body);

    // Check validation
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }
    const code = req.body.code;
    Project.findOne({ code: dbsanitize(req.body.code), 'status': { $ne: 'delete' }, 'owner': dbsanitize(req.user.email) }).then(proj => {
        if (!proj) {
            errors[code] = "Project not found.";
            return res.status(400).json(errors);
        } else {
            proj.name = req.body.name;
            proj.desc = req.body.desc;
            proj.status = req.body.status;
            proj.public = req.body.public;
            proj.sharedto = req.body.sharedto;

            proj.updated = Date.now();
            proj.save().then(proj => {
                return res.json({
                    success: true,
                });
            }).catch(err => {
                errors[code] = "Failed to update project.";
                return res.status(400).json(errors);
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/project/info
// @access Private
router.post("/project/info", (req, res) => {
    logger.debug("/auth-api/user/project/info: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    //find all project owned by user and shared to user
    Project.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }, { 'public': true }]
    }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }
        return res.send(project);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  auth-api/user/project/runstats
// @access Private
router.post("/project/runstats", (req, res) => {
    logger.debug("/auth-api/user/project/runstats: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) },
        { 'public': true }]
    }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = common.runStats(project);
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});
// @route POST  auth-api/user/project/conf
// @access Private
router.post("/project/conf", (req, res) => {
    logger.debug("/auth-api/user/project/conf: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) },
        { 'public': true }]
    }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = common.conf(project);
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  auth-api/user/project/result
// @access Private
router.post("/project/result", (req, res) => {
    logger.debug("/auth-api/user/project/result: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) },
        { 'public': true }]
    }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = { "result": common.projectResult(project) };
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});


//files
// @route POST auth-api/user/upload/list
// @access Private
router.get("/upload/list", (req, res) => {
    logger.debug("/auth-api/user/upload/list: " + JSON.stringify(req.body));
    //find all uploaded files owned by user
    Upload.find({ 'status': { $ne: 'delete' }, 'owner': dbsanitize(req.user.email) }).sort([['updated', -1]]).then(function (files) {
        return res.send(files);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route GET auth-api/user/upload/info
// @access Private
router.get("/upload/info", (req, res) => {
    logger.debug("/auth-api/user/upload/info: " + JSON.stringify(req.body));
    getUploadedSize(req.user.email, function (size) {
        if (isNaN(size)) {
            return res.status(500).json(sysError);
        } else {
            return res.json({
                uploadedSize: size,
                maxStorageSizeBytes: config.FILE_UPLOADS.MAX_STORAGE_SIZE_BYTES,
                daysKept: config.FILE_UPLOADS.FILE_LIFETIME_DAYS,
                maxFileSizeBytes: config.FILE_UPLOADS.MAX_FILE_SIZE_BYTES
            })
        }
    });
});

function getUploadedSize(owner, callback) {
    //find all uploaded files owned by user
    Upload.aggregate([{
        $match: { $and: [{ 'status': { $ne: 'delete' }, 'owner': owner }] },
    }, {
        $group: {
            _id: null,
            total: {
                $sum: "$size"
            }
        }
    }],
        function (err, result) {
            let size = 0;
            if (err) {
                size = sysError;
            } else {
                if (result[0]) {
                    size = result[0].total;
                }
            }
            return callback(size)
        });
}

//upload files
// @route POST auth-api/upload/add
// @desc Add new upload file
// @access Private
router.post("/upload/add", (req, res) => {
    logger.debug("/auth-api/user/upload/add: " + JSON.stringify(req.body));
    // Form validation
    const { errors, isValid } = validateAdduploadInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }

    //check storage size
    getUploadedSize(req.user.email, function (size) {
        if (isNaN(size)) {
            return res.status(500).json(sysError);
        } else {
            let newSize = Number(size) + Number(req.body.size);
            if (newSize > config.FILE_UPLOADS.MAX_STORAGE_SIZE_BYTES) {
                return res.status(400).json("Storage limit exceeded.");
            }

            //upload file
            let code = randomize('Aa0', 16) + "." + req.body.type;
            let upload_home = path.join(config.IO.UPLOADED_FILES_DIR, code);
            while (fs.existsSync(upload_home)) {
                code = randomize('Aa0', 16);
                upload_home = path.join(config.IO.UPLOADED_FILES_DIR, code);
            }

            const newData = new Upload({
                name: req.body.name,
                type: req.body.type,
                size: req.body.size,
                owner: req.user.email,
                code: code
            });
            newData
                .save()
                .then(upload => {
                    //save uploaded file
                    const file = req.files.file;
                    file.mv(`${upload_home}`, err => {
                        if (err) {
                            logger.error(err);
                            return res.status(500).json(sysError);
                        }
                        logger.debug("upload:" + `${upload_home}`);
                        return res.json({
                            success: true,
                        });
                    })
                })
                .catch(err => {
                    logger.error(err);
                    return res.status(500).json(sysError);
                });
        }
    });
});

// @route POST auth-api/user/upload/delete
// @desc delete user account 
// @access Private
//will not use this function to avoid delete a shared file using by other users
router.post("/upload/delete", (req, res) => {
    logger.debug("/auth-api/user/upload/delete: " + JSON.stringify(req.body));
    const code = dbsanitize(req.body.code);
    if (!code) {
        return res.status(400).json("Upload code is required.");
    }

    Upload.findOne({ code: code }).then(file => {
        let errors = {};
        if (!file) {
            errors[code] = "Upload not found.";
            return res.status(400).json(errors);
        } else if (file.owner !== req.user.email) {
            errors[code] = "Only file owner can perform this action.";
            return res.status(400).json(errors);
        } else {
            //mark as delete
            Upload.findOne({ code: code }).then(upload => {
                if (!upload) {
                    logger.debug("Upload not found." + code);
                } else {
                    upload.status = 'delete';
                    upload.updated = Date.now();
                    upload.save().then(file => {
                        return res.json({
                            success: true,
                        });
                    }).catch(err => {
                        logger.error("Failed to update upload." + code);
                        logger.error(err);
                        return res.status(500).json(sysError);
                    });
                }
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/upload/update
// @desc delete user account 
// @access Private
router.post("/upload/update", (req, res) => {
    logger.debug("/auth-api/user/upload/update: " + JSON.stringify(req.body));
    const code = dbsanitize(req.body.code);
    if (!code) {
        return res.status(400).json("Upload code is required.");
    }
    Upload.findOne({ 'status': { $ne: 'delete' }, code: code, 'owner': dbsanitize(req.user.email) }).then(upload => {
        let errors = {};
        if (!upload) {
            errors[code] = "Upload not found.";
            return res.status(400).json(errors);
        } else {
            upload.name = req.body.name;
            upload.desc = req.body.desc;
            upload.public = req.body.public;
            upload.sharedto = req.body.sharedto;
            if (req.body.status) {
                upload.status = req.body.status;
            }

            upload.updated = Date.now();
            upload.save().then(upload => {
                return res.json({
                    success: true,
                });
            }).catch(err => {
                logger.error("Failed to update upload." + err);
                errors[code] = "Failed to update upload.";
                return res.status(400).json(errors);
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

//find all files matching fileTypes in project directories
// @route POST auth-api/user/project/files
// @access Private
router.post("/project/files", (req, res) => {
    logger.debug("/auth-api/user/project/files: " + JSON.stringify(req.body));
    const proj_dir = config.PROJECTS.BASE_DIR;
    let projStatuses = ['complete'];
    if (req.body.projectStatuses) {
        projStatuses = req.body.projectStatuses;
    }
    let query = { 'status': { $in: projStatuses }, $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }, { 'public': true }] };
    if (req.body.projectScope === 'self') {
        query = { 'status': { $in: projStatuses }, $or: [{ 'owner': dbsanitize(req.user.email) }] };
    } else if (req.body.projectScope === 'self+shared') {
        query = { 'status': { $in: projStatuses }, $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }] };
    }
    if (req.body.projectTypes) {
        query.type = { $in: req.body.projectTypes };
    }
    if (req.body.projectCodes) {
        query.code = { $in: req.body.projectCodes };
    }

    Project.find(query).sort([['name', -1]]).then(function (projects) {
        let files = [];
        var i = 0;
        //make sure the FileBrowser key is unique
        for (i; i < projects.length; i++) {
            const proj = projects[i];
            let projName = proj.owner + '/' + proj.name;
            // get project output dir
            let outdir = '';
            Object.keys(workflowlist).forEach((key) => {
                if(workflowlist[key]['full_name'] === proj.type) {
                    outdir = workflowlist[key]['outdir'];
                }
            });
            if (proj.type === 'Retrieve SRA Data') {
                projName += " (" + moment(proj.created).format('YYYY-MM-DD, h:mm:ss A') + ")";
                files = common.getAllFiles(proj_dir + '/' + proj.code + '/' + outdir, files, req.body.fileTypes, "sradata/" + projName, '/sradata/' + proj.code + '/' + outdir, proj_dir + "/" + proj.code + '/' + outdir, req.body.endsWith);
            } else {
                projName += " (" + proj.type + ", " + moment(proj.created).format('YYYY-MM-DD, h:mm:ss A') + ")";
                files = common.getAllFiles(proj_dir + '/' + proj.code + '/' + outdir, files, req.body.fileTypes, "projects/" + projName, '/projects/' + proj.code + '/' + outdir, proj_dir + "/" + proj.code + '/' + outdir, req.body.endsWith);
            }
        };
        return res.send({ fileData: files });
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

//find all output files in a project 
// @route POST auth-api/user/project/files
// @access Private
router.post("/project/outputs", (req, res) => {
    logger.debug("/auth-api/user/project/outputs: " + JSON.stringify(req.body));
    const proj_dir = config.PROJECTS.BASE_DIR;
    let query = { 'code': req.body.code, 'status': { $ne: 'delete' }, $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }, { 'public': true }] };

    Project.find(query).sort([['name', -1]]).then(function (projects) {
        let files = [];
        const proj = projects[0];
        if (proj && fs.existsSync(proj_dir + '/' + proj.code + '/output')) {
            files = common.getAllFiles(proj_dir + '/' + proj.code + '/output', files, req.body.fileTypes, '', '/projects/' + proj.code + '/output', proj_dir + "/" + proj.code + '/output');
        }
        return res.send({ fileData: files });
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/upload/files
// @access Private
//all upload files user can access to
router.post("/upload/files", (req, res) => {
    logger.debug("/auth-api/user/upload/files: " + JSON.stringify(req.body));
    //find all files owned by user and shared to user or public
    const upload_dir = config.IO.UPLOADED_FILES_DIR;
    //find all uploaded files available to user
    let query = { 'status': { $ne: 'delete' }, $or: [{ 'owner': dbsanitize(req.user.email) }, { 'sharedto': dbsanitize(req.user.email) }, { 'public': true }] };
    if (req.body.fileTypes) {
        if (req.body.endsWith) {
            query.name = { $regex: req.body.fileTypes[0] };
        } else {
            query.type = { $in: req.body.fileTypes };
        }
    }

    Upload.find(query).sort([['updated', -1]]).then(function (uploads) {
        let files = [];
        var i = 0;
        //make sure the FileBrowser key is unique
        let fNameMap = new Map();
        for (i; i < uploads.length; i++) {
            const upload = uploads[i];
            let fName = upload.name;
            let cnt = fNameMap.get(fName);
            if (cnt) {
                fName += " (" + cnt + ")";
                cnt++;
            } else {
                cnt = 1;
            }
            fNameMap.set(upload.name, cnt);

            const file = upload_dir + '/' + upload.code;
            if (fs.existsSync(file)) {
                var stats = fs.statSync(file)
                let dfile = {
                    key: 'uploads/' + upload.owner + "/" + fName, path: "uploads/" + upload.code,
                    filePath: upload_dir + "/" + upload.code, size: stats.size, modified: Number(new Date(stats.mtime))
                };
                files.push(dfile);
            }
        };

        return res.send({ fileData: files });
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/user/data/files
// @access Private
//all public files user can access to
router.post("/data/files", (req, res) => {
    logger.debug("/auth-api/user/data/files: " + JSON.stringify(req.body));
    const data_dir = config.IO.PUBLIC_BASE_DIR;
    const files = common.getAllFiles(data_dir, [], req.body.fileTypes, "publicdata", "publicdata", data_dir, req.body.endsWith);

    return res.send({ fileData: files });
});

// @route POST auth-api/user/globus/files
// @access Private
//all globus files user can access to
router.post("/globus/files", (req, res) => {
    logger.debug("/auth-api/user/globus/files: " + JSON.stringify(req.body));
    const data_dir = config.GLOBUS.DATA_HOME_DIR + "/" + req.user.email;
    let files = [];
    if (fs.existsSync(data_dir)) {
        files = common.getAllFiles(data_dir, [], req.body.fileTypes, "globus", "globus", data_dir, req.body.endsWith);
    }

    return res.send({ fileData: files });
});

module.exports = router;