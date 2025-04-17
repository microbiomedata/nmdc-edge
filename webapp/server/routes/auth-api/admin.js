const express = require("express");
const router = express.Router();
const randomize = require('randomatic');
const dbsanitize = require('mongo-sanitize');
const User = require("../../models/User");
const Project = require("../../models/Project");
const Upload = require("../../models/Upload");
const validateAdduserInput = require("../../validation/admin/adduser");
const validateUpdateuserInput = require("../../validation/admin/updateuser");
const validateDeleteuserInput = require("../../validation/admin/deleteuser");
const validateUpdateprojectInput = require("../../validation/admin/updateproject");
const isEmpty = require("is-empty");

const common = require("../common");
const logger = require('../../util/logger');
const config = require("../../config");
const BulkSubmission = require("../../models/BulkSubmission");

const sysError = "API server error";

// @route GET auth-api/admin/user/list
// @access Private
router.get("/user/list", (req, res) => {
    logger.debug("/auth-api/admin/user/list: " + JSON.stringify(req.body));
    //get all users
    User.find({}).sort([['updated', -1]]).then(function (users) {
        return res.send(users);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/user/add
// @desc Register user
// @access Private
router.post("/user/add", (req, res) => {
    // Form validation
    const { errors, isValid } = validateAdduserInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }

    logger.debug("/auth-api/admin/user/add: " + JSON.stringify(req.body.email));
    User.findOne({ email: dbsanitize(req.body.email) }).then(user => {
        if (user) {
            return res.status(400).json("Email already exists");
        } else {
            var code = randomize("0", 6);
            const newUser = new User({
                firstname: req.body.firstname,
                lastname: req.body.lastname,
                email: req.body.email,
                mailto: req.body.email,
                password: req.body.password,
                status: req.body.status,
                type: req.body.type,
                code: code
            });

            // Hash password before saving in database
            common.encodePassword(newUser.password).then(hash => {
                newUser.password = hash;
                newUser
                    .save()
                    .then(user => {
                        return res.json({ user: user })
                    })
                    .catch(err => {
                        logger.error(err);
                        return res.status(500).json(sysError);
                    });
            }).catch(err => {
                logger.error(err);
                return res.status(500).json(sysError);
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/user/update
// @desc update user account 
// @access Private
router.post("/user/update", (req, res) => {
    // Form validation
    const { errors, isValid } = validateUpdateuserInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }
    logger.debug("/auth-api/admin/user/update: " + JSON.stringify(req.body.email));

    User.findOne({ email: dbsanitize(req.body.email) }).then(user => {
        if (!user) {
            return res.status(400).json("User not found.");
        } else {
            user.code = randomize("0", 6);
            user.firstname = req.body.firstname;
            user.lastname = req.body.lastname;
            if (!isEmpty(req.body.type)) {
                user.type = req.body.type;
            }
            if (!isEmpty(req.body.status)) {
                user.status = req.body.status;
            }

            user.updated = Date.now();
            if (!isEmpty(req.body.password)) {
                // Hash password before saving in database
                common.encodePassword(req.body.password).then(hash => {
                    user.password = hash;

                    user.save().then(user => {
                        return res.json({
                            success: true,
                        });
                    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
                }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
            } else {
                user.save().then(user => {
                    return res.json({
                        success: true,
                    });
                }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
            }
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/user/delete
// @desc delete user account 
// @access Private
router.post("/user/delete", (req, res) => {
    // Form validation
    const { errors, isValid } = validateDeleteuserInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }

    logger.debug("/auth-api/admin/user/delete: " + JSON.stringify(req.body.email));
    User.findOne({ email: dbsanitize(req.body.email) }).then(user => {
        if (!user) {
            return res.status(400).json("User not found.");
        } else {
            //find all projects associated with this user
            Project.find({ 'status': { $ne: 'delete' }, owner: user.email }).count(function (err, count) {
                if (err) {
                    logger.error(err);
                    return res.status(500).json(sysError);
                } else {
                    if (count === 0) {
                        //check uploaded files
                        Upload.find({ 'status': { $ne: 'delete' }, owner: user.email }).count(function (err, count) {
                            if (err) {
                                logger.error(err);
                                return res.status(500).json(sysError);
                            } else {
                                if (count === 0) {
                                    User.deleteOne({ email: user.email }, function (err) {
                                        if (err) {
                                            logger.error("delete user failed: " + err);
                                            return res.status(500).json(sysError);
                                        } else {
                                            return res.json({
                                                success: true,
                                            });
                                        }
                                    });
                                } else if (count === 1) {
                                    return res.status(400).json({ error: "There is 1 upload associated with user " + user.email });
                                } else {
                                    return res.status(400).json({ error: "There are " + count + " uploads associated with user " + user.email });
                                }
                            }
                        });

                    } else if (count === 1) {
                        return res.status(400).json({ error: "There is 1 project associated with user " + user.email });
                    } else {

                        return res.status(400).json({ error: "There are " + count + " projects associated with user " + user.email });
                    }
                }
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/project/list
// @access Private
router.get("/project/list", (req, res) => {
    logger.debug("/auth-api/admin/project/list: " + JSON.stringify(req.body));
    //get all projects
    Project.find({ 'status': { $ne: 'delete' } }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/project/update
// @desc update project 
// @access Private
router.post("/project/update", (req, res) => {
    //assume project code is provided
    let { errors, isValid } = validateUpdateprojectInput(req.body);
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }

    logger.debug("/auth-api/admin/project/update: " + JSON.stringify(req.body.code));
    Project.findOne({ code: dbsanitize(req.body.code) }).then(proj => {
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
            }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/project/info
// @access Private
router.post("/project/info", (req, res) => {
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    logger.debug("/auth-api/admin/project/info: " + JSON.stringify(req.body.code));
    //find project
    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code) }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }
        return res.send(project);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  auth-api/admin/project/runstats
// @access Private
router.post("/project/runstats", (req, res) => {
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    logger.debug("/auth-api/admin/project/runstats: " + JSON.stringify(req.body.code));

    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code) }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = common.runStats(project);
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  auth-api/admin/project/conf
// @access Private
router.post("/project/conf", (req, res) => {
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    logger.debug("/auth-api/admin/project/conf: " + JSON.stringify(req.body.code));

    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code) }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = common.conf(project);
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});
// @route POST  auth-api/admin/project/result
// @access Private
router.post("/project/result", (req, res) => {
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    logger.debug("/auth-api/admin/project/result: " + JSON.stringify(req.body.code));

    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code) }, { 'sharedto': 0 }).then(function (project) {
        if (project === null) {
            return res.status(400).json("Project not found.");
        }

        let result = { "result": common.projectResult(project) };
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

//find all output files in a project 
// @route POST auth-api/user/project/files
// @access Private
router.post("/project/outputs", (req, res) => {
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    logger.debug("/auth-api/admin/project/outputs: " + JSON.stringify(req.body.code));
    const proj_dir = config.PROJECTS.BASE_DIR;
    let query = { 'code': req.body.code, 'status': { $ne: 'delete' } };

    Project.find(query).sort([['name', -1]]).then(function (projects) {
        let files = [];
        const proj = projects[0];
        if (proj) {
            files = common.getAllFiles(proj_dir + '/' + proj.code + '/output', files, req.body.fileTypes, '', '/projects/' + proj.code + '/output', proj_dir + "/" + proj.code + '/output');
        }
        return res.send({ fileData: files });
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

//upload files
// @route POST auth-api/admin/upload/list
// @access Private
router.get("/upload/list", (req, res) => {
    logger.debug("/auth-api/admin/upload/list: " + JSON.stringify(req.body));
    Upload.find({ 'status': { $ne: 'delete' } }).sort([['updated', -1]]).then(function (uploads) {
        return res.send(uploads);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/upload/update
// @desc update data
// @access Private
router.post("/upload/update", (req, res) => {
    const code = dbsanitize(req.body.code);
    if (!code) {
        return res.status(400).json("Upload code is required.");
    }
    logger.debug("/auth-api/admin/upload/update: " + JSON.stringify(req.body.code));
    Upload.findOne({ 'status': { $ne: 'delete' }, code: code }).then(upload => {
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
                errors[code] = "Failed to update upload.";
                return res.status(400).json(errors);
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/bulkSubmission/list
// @access Private
router.get("/bulkSubmission/list", (req, res) => {
    logger.debug("/auth-api/admin/bulkSubmission/list: " + JSON.stringify(req.body));
    //get all bulkSubmissions
    BulkSubmission.find({ 'status': { $ne: 'delete' } }).sort([['updated', -1]]).then(function (bulkSubmissions) {
        return res.send(bulkSubmissions);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/bulkSubmission/update
// @desc update bulkSubmission 
// @access Private
router.post("/bulkSubmission/update", (req, res) => {
    logger.debug("/auth-api/admin/bulkSubmission/update: " + JSON.stringify(req.body));
    //assume project code is provided
    const code = req.body.code;
    BulkSubmission.findOne({ code: dbsanitize(req.body.code), 'status': { $ne: 'delete' } }).then(bulkSubmission => {
        if (!bulkSubmission) {
            errors[code] = "BulkSubmission not found.";
            return res.status(400).json(errors);
        } else {
            bulkSubmission.name = req.body.name;
            bulkSubmission.desc = req.body.desc;
            bulkSubmission.status = req.body.status;

            bulkSubmission.updated = Date.now();
            bulkSubmission.save().then(proj => {
                return res.json({
                    success: true,
                });
            }).catch(err => {
                errors[code] = "Failed to update bulkSubmission.";
                return res.status(400).json(errors);
            });
        }
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/bulkSubmission/projects
// @access Private
//projects in bulk submission
router.post("/bulkSubmission/projects", async (req, res) => {
    logger.debug("/auth-api/admin/bulkSubmission/projects: " + JSON.stringify(req.body));
    //find project codes in bulk submission
    const bulkSubmission = await BulkSubmission.findOne({ 'code': req.body.code });
    //return projects
    if (!bulkSubmission.projects || bulkSubmission.projects.length === 0) {
        return res.send([]);
    }
    Project.find({ 'code': { $in: bulkSubmission.projects } }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST auth-api/admin/bulkSubmission/info
// @access Private
router.post("/bulkSubmission/info", (req, res) => {
    logger.debug("/auth-api/admin/bulkSubmission/info: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("BulkSubmission code is required.");
    }
    //find bulkSubmission 
    BulkSubmission.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code)
    }).then(function (bulkSubmission) {
        if (bulkSubmission === null) {
            return res.status(400).json("BulkSubmission not found.");
        }
        return res.send(bulkSubmission);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  auth-api/admin/bulkSubmission/conf
// @access Private
router.post("/bulkSubmission/conf", (req, res) => {
    logger.debug("/auth-api/admin/bulkSubmission/conf: " + JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("BulkSubmission code is required.");
    }
    BulkSubmission.findOne({
        'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code)
    }).then(function (bulkSubmission) {
        if (bulkSubmission === null) {
            return res.status(400).json("BulkSubmission not found.");
        }

        let result = common.bulkSubmissionConf(bulkSubmission);
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

module.exports = router;