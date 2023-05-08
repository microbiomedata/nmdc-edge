const fs = require('fs');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const common = require("../util/common");
const { generateWorkflowResult, generatePipelineResult } = require("../util/workflow");
const logger = require('../util/logger');

module.exports = function cromwellMonitor() {
    logger.debug("cromwell monitor");

    //only process one job at each time based on job updated time
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] } }).sort({ updated: 1 }).then(jobs => {
        let job = jobs[0];
        if (!job) {
            logger.debug("No cromwell job to process");
            return;
        }
        logger.debug("cromwell " + job);
        //find related project
        Project.findOne({ 'code': job.project }).then(proj => {
            if (proj) {
                if (proj.status === 'delete') {
                    //abort job
                    abortJob(job);
                } else {
                    updateJobStatus(job, proj);
                }
            } else {
                //delete from database
                CromwellJob.deleteOne({ project: job.project }, function (err) {
                    if (err) {
                        logger.error("Failed to delete job from DB " + job.project + ":" + err);
                    }
                });

            }
        });
    });
};

function updateJobStatus(job, proj) {
    //get job status through api
    logger.debug("GET: " + process.env.CROMWELL_API_URL + "/" + job.id + "/status");
    common.getData(process.env.CROMWELL_API_URL + "/" + job.id + "/status").then(response => {
        logger.debug(JSON.stringify(response));
        //update project status
        if (job.status !== response.status) {
            let status = null;
            if (response.status === 'Running') {
                status = 'running';
            } else if (response.status === 'Succeeded') {
                //generate result.json
                logger.info("generate workflow result.json");
                try {
                    if (proj.type.match(/Pipeline$/)) {
                        generatePipelineResult(proj);
                    } else {
                        generateWorkflowResult(proj);
                    }
                } catch (e) {
                    job.status = response.status;
                    job.updated = Date.now();
                    job.save();
                    //result not as expected
                    proj.status = 'failed';
                    proj.updated = Date.now();
                    proj.save();
                    throw e;
                }
                status = 'complete';
            } else if (response.status === 'Failed') {
                status = 'failed';
            } else if (response.status === 'Aborted') {
                status = 'in queue';
            }
            proj.status = status;
            proj.updated = Date.now();
            proj.save();
            common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", "Cromwell job status: " + response.status);
        }
        //update job even its status unchanged. We need set new updated time for this job.
        if (response.status === 'Aborted') {
            //delete job
            CromwellJob.deleteOne({ project: proj.code }, function (err) {
                if (err) {
                    logger.error("Failed to delete job from DB " + proj.code + ":" + err);
                }
            });
        } else {
            job.status = response.status;
            job.updated = Date.now();
            job.save();
            getJobMetadata(job);
        }
    }).catch(error => {
        let message = error;
        if (error.message) {
            message = error.message;
        }
        common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", message);
        logger.error(message);
    });
}

function abortJob(job) {
    //abort job through api
    logger.debug("POST: " + process.env.CROMWELL_API_URL + "/" + job.id + "/abort");
    common.postData(process.env.CROMWELL_API_URL + "/" + job.id + "/abort").then(response => {
        //update job status
        job.status = "Aborted";
        job.updated = Date.now();
        job.save();
        common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", "Cromwell job aborted.");
    }).catch(error => {
        let message = error;
        if (error.message) {
            message = error.message;
        }
        common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", message);
        logger.error(message);
        //not cromwell api server error, job may already complete/fail
        if (error.status !== 500) {
            job.status = "Aborted";
            job.updated = Date.now();
            job.save();
            common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", "Cromwell job aborted.");
        }
    });
}

function getJobMetadata(job) {
    //get job metadata through api
    logger.debug("GET: " + process.env.CROMWELL_API_URL + "/" + job.id + "/metadata");
    common.getData(process.env.CROMWELL_API_URL + "/" + job.id + "/metadata").then(metadata => {
        //logger.debug(JSON.stringify(metadata));
        logger.debug(process.env.PROJECT_HOME + "/" + job.project + '/cromwell_job_metadata.json');
        fs.writeFileSync(process.env.PROJECT_HOME + "/" + job.project + '/cromwell_job_metadata.json', JSON.stringify(metadata));

        //dump error logs
        Object.keys(metadata['calls']).map((callkey, keyindex) => {
            let subStatus = metadata['calls'][callkey][0]['executionStatus'];
            let subId = metadata['calls'][callkey][0]['subWorkflowId'];

            //get cromwell logs
            if (subStatus === 'Failed' && subId) {
                logger.debug("GET: " + process.env.CROMWELL_API_URL + "/" + subId + "/logs");
                common.getData(process.env.CROMWELL_API_URL + "/" + subId + "/logs").then(logs => {
                    logger.debug(JSON.stringify(logs));
                    fs.writeFileSync(process.env.PROJECT_HOME + "/" + job.project + '/' + callkey + '.cromwell_job_logs.json', JSON.stringify(logs));
                    //dump stderr to log.txt
                    Object.keys(logs['calls']).map((call, index) => {
                        logger.debug(call);
                        logs['calls'][call].forEach(item => {
                            let stderr = item['stderr'];
                            logger.debug(stderr);
                            if (fs.existsSync(stderr)) {
                                const errs = fs.readFileSync(stderr);
                                common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", call);
                                common.write2log(process.env.PROJECT_HOME + "/" + job.project + "/log.txt", errs);
                            }
                        });
                    });
                }).catch(error => {
                    logger.error("Failed to get logs from Cromwell API");
                });
            }
        });

    }).catch(error => {
        logger.error("Failed to get metadata from Cromwell API");
    });
}