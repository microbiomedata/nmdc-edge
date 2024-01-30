const express = require("express");
const router = express.Router();
const fs = require('fs');
const dbsanitize = require('mongo-sanitize');
const Project = require("../../models/Project");

const common = require("../common");
const logger = require("../../util/logger");
const config = require("../../config");

const sysError = "API server error";

// @route POST api/project/list
// @access Public
router.get("/list", (req, res) => {
    logger.debug("/api/project/list", JSON.stringify(req.body));
    Project.find({ 'status': { $ne: 'delete' }, 'public': true }, { 'sharedto': 0 }).sort([['updated', -1]]).then(function (projects) {
        return res.send(projects);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  api/project/info
// @access Public
router.post("/info", (req, res) => {
    logger.debug("/api/project/info", JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), 'public': true }, { 'sharedto': 0 }).then(function (project) {
        if(project === null) {
            logger.debug("Project not found");
            return res.status(400).json("Project not found.");
        }
        return res.send(project);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  api/project/runstats
// @access Public
router.post("/runstats", (req, res) => {
    logger.debug("/api/project/runstats", JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), 'public': true }, { 'sharedto': 0 }).then(function (project) {
        if(project === null) {
            logger.debug("Project not found");
            return res.status(400).json("Project not found.");
        }

        let result = common.runStats(project) ;
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  api/project/conf
// @access Public
router.post("/conf", (req, res) => {
    logger.debug("/api/project/conf", JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), 'public': true }, { 'sharedto': 0 }).then(function (project) {
        if(project === null) {
            logger.debug("Project not found");
            return res.status(400).json("Project not found.");
        }

        let result = common.conf(project) ;
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

// @route POST  api/project/result
// @access Public
router.post("/result", (req, res) => {
    logger.debug("/api/project/result", JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    Project.findOne({ 'status': { $ne: 'delete' }, 'code': dbsanitize(req.body.code), 'public': true }, { 'sharedto': 0 }).then(function (project) {
        if(project === null) {
            logger.debug("Project not found");
            return res.status(400).json("Project not found.");
        }

        let result = { "result": common.projectResult(project) };
        return res.send(result);
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

//find all output files in a project 
// @route POST auth-api/user/project/files
// @access Private
router.post("/outputs", (req, res) => {
    logger.debug("/api/project/outputs", JSON.stringify(req.body));
    if (!req.body.code) {
        return res.status(400).json("Project code is required.");
    }
    const proj_dir = config.PROJECTS.BASE_DIR;
    let query = { 'code': req.body.code, 'status': { $ne: 'delete' }, 'public': true };

    Project.find(query).sort([['name', -1]]).then(function (projects) {
        let files = [];
        const proj = projects[0];
        if (proj) {
            files = common.getAllFiles(proj_dir + '/' + proj.code + '/output', files, req.body.fileTypes, '', '/projects/' + proj.code + '/output', proj_dir + "/" + proj.code + '/output');
        }
        return res.send({ fileData: files });
    }).catch(err => { logger.error(err); return res.status(500).json(sysError); });
});

module.exports = router;