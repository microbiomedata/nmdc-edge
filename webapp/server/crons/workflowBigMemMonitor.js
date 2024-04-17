const fs = require('fs');
const path = require('path');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const { workflowlist } = require("../config/workflow");
const common = require("../util/common");
const logger = require('../util/logger');
const { generateWDL, generateInputs, submitWorkflow, findInputsize } = require("../util/workflow");
const config = require("../config");

module.exports = function workflowBigMemMonitor() {
    logger.debug("workflow big mem monitor");
    //only process one job at each time based on job updated time
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] }, 'type': { $in: ['virus_plasmid'] } }).sort({ updated: 1 }).then(jobs => {
        //submit request only when the current cromwell running jobs less than the max allowed jobs
        if (jobs.length >= config.CROMWELL.NUM_BIG_MEM_JOBS_MAX) {
            return;
        }
        //get current running/submitted projects' input size
        let jobInputsize = 0;
        jobs.forEach(job => {
            jobInputsize += job.inputsize;
        });
        //only process one request at each time
        Project.find({ 'type': { $in: ['virus_plasmid'] }, 'status': 'in queue' }).sort({ updated: 1 }).then(async projs => {
            let proj = projs[0];
            if (!proj) {
                logger.debug("No workflow big mem request to process");
                return;
            }
            //parse conf.json
            const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
            const conf_file = proj_home + "/conf.json";
            let rawdata = fs.readFileSync(conf_file);
            let projConf = JSON.parse(rawdata);

            //check input size
            let inputsize = await findInputsize(projConf);
            if (inputsize > config.CROMWELL.JOBS_INPUT_MAX_SIZE_BYTES) {
                logger.debug("Project " + proj.code + " input size exceeded the limit.");
                //fail project
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "input size exceeded the limit.");
                return;
            }
            if ((jobInputsize + inputsize) > config.CROMWELL.JOBS_INPUT_MAX_SIZE_BYTES) {
                logger.debug("Cromwell is busy.");
                return;
            }

            logger.info("Processing workflow request: " + proj.code)
            //set project status to 'processing'
            proj.status = "processing";
            proj.updated = Date.now();
            proj.save().then(proj => {
                common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "Generate WDL and inputs json");
                logger.info("Generate WDL and inputs json");
                //process request
                const workflow = projConf.workflow;
                //create output directory
                fs.mkdirSync(proj_home + "/" + workflowlist[workflow.name]['outdir'], { recursive: true });
                //in case cromwell needs permission to write to the output directory
                fs.chmodSync(proj_home + "/" + workflowlist[workflow.name]['outdir'], '777');
                //generate pipeline.wdl and inputs.json
                let promise1 = new Promise(function (resolve, reject) {
                    const wdl = generateWDL(proj_home, workflow);
                    if (wdl) {
                        resolve(proj);
                    } else {
                        reject("Failed to generate WDL for project " + proj.code);
                    }
                });
                let promise2 = new Promise(function (resolve, reject) {
                    generateInputs(proj_home, projConf, proj).then(inputs => {
                        if (inputs) {
                            resolve(proj);
                        } else {
                            reject("Failed to generate inputs.json for project " + proj.code);
                        }
                    })
                });

                Promise.all([promise1, promise2]).then(function (projs) {
                    //submit workflow to cromwell
                    common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "submit workflow to cromwell");
                    logger.info("submit workflow to cromwell");
                    submitWorkflow(proj, workflow, inputsize);
                }).catch(function (err) {
                    proj.status = 'failed';
                    proj.updated = Date.now();
                    proj.save();
                    common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), err);
                    logger.error(err);
                });
            }).catch(err => {
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), err);
                logger.error(err);
            });
        });
    });
};