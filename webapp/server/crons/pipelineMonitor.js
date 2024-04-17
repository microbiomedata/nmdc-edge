const fs = require('fs');
const path = require('path');
const ejs = require('ejs');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const { workflowlist, pipelinelist } = require("../config/workflow");
const common = require("../util/common");
const logger = require('../util/logger');
const { submitWorkflow, findInputsize } = require("../util/workflow");
const config = require("../config");

module.exports = function pipelineMonitor() {
    logger.debug("pipeline monitor");
    //only process one job at each time based on job updated time
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] } }).sort({ updated: 1 }).then(jobs => {
        if (jobs.length >= config.CROMWELL.NUM_JOBS_MAX) {
            return;
        }
        //get current running/submitted projects' input size
        let jobInputsize = 0;
        jobs.forEach(job => {
            jobInputsize += job.inputsize;
        });

        //only process one request at each time
        Project.find({ 'type': 'Metagenome Pipeline', 'status': 'in queue' }).sort({ updated: 1 }).then(async projs => {
            let proj = projs[0];
            if (!proj) {
                logger.debug("No pipeline request to process");
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
                logger.debug("Project " + proj.code + " input fastq size exceeded the limit.");
                //fail project
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "input fastq size exceeded the limit.");
                return;
            }
            if ((jobInputsize + inputsize) > config.CROMWELL.JOBS_INPUT_MAX_SIZE_BYTES) {
                logger.debug("Cromwell is busy.");
                return;
            }

            logger.info("Processing pipeline request: " + proj.code);

            //set project status to 'processing'
            proj.status = "processing";
            proj.updated = Date.now();
            proj.save().then(proj => {
                common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "Generate WDL and inputs json");
                logger.info("Generate WDL and inputs json");
                //process request 
                const pipeline = projConf.pipeline;
                //create output directory
                fs.mkdirSync(proj_home + "/" + pipelinelist[pipeline]['outdir'], { recursive: true });
                //in case cromwell needs permission to write to the output directory
                fs.chmodSync(proj_home + "/" + pipelinelist[pipeline]['outdir'], '777');
                //generate pipeline.wdl and inputs.json
                let promise1 = new Promise(function (resolve, reject) {
                    const wdl = generateWDL(proj_home, pipeline);
                    if (wdl) {
                        resolve(proj);
                    } else {
                        logger.error("Failed to generate WDL for project " + proj.code);
                        reject("Failed to generate WDL for project " + proj.code);
                    }
                });
                let promise2 = new Promise(function (resolve, reject) {
                    generateInputs(proj_home, projConf, proj).then(inputs => {
                        if (inputs) {
                            resolve(proj);
                        } else {
                            logger.error("Failed to generate inputs.json for project " + proj.code);
                            reject("Failed to generate inputs.json for project " + proj.code);
                        }
                    }).catch(function (err) {
                        throw new Error(err);
                    });
                });

                Promise.all([promise1, promise2]).then(function (projs) {
                    //submit workflow to cromwell
                    common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), "submit workflow to cromwell");
                    logger.info("submit workflow to cromwell");
                    submitWorkflow(proj, pipeline, inputsize);
                }).catch(function (err) {
                    throw new Error("Failed to submit workflow to cromwell");
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

function generateWDL(proj_home, pipeline) {
    //build wdl
    const pipelineSettings = pipelinelist[pipeline];
    const main_wdl = path.join(config.WORKFLOWS.WDL_DIR, pipelineSettings['main_wdl'] ? pipelineSettings['main_wdl'] : "notfound");
    if (fs.existsSync(main_wdl)) {
        // copy main wdl to <project>/pipeline.wdl
        // fs.copyFileSync(main_wdl, proj_home + '/pipeline.wdl');
        // add pipeline.wdl link
        fs.symlinkSync(main_wdl, proj_home + '/pipeline.wdl', 'file');
        return true;
    }
    logger.error("workflow pipeline template not found: " + main_wdl);
    return false;
}

async function generateInputs(proj_home, projectConf, proj) {
    // projectConf: <project>/conf.js
    // pipelinelist: config/workflow.js
    // commonConf: data/workflow/templates/common.json
    const pipelineSettings = pipelinelist[projectConf.pipeline];
    const commonConf = JSON.parse(fs.readFileSync(config.WORKFLOWS.COMMON));
    const tmpl_inputs = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelineSettings['inputs_tmpl'] ? pipelineSettings['inputs_tmpl'] : "notfound");
    if (!fs.existsSync(tmpl_inputs)) {
        logger.error("Pipeline inputs template not found: " + tmpl_inputs);
        return false;
    }
    const template = String(fs.readFileSync(tmpl_inputs));
    const params = { ...commonConf, outdir: `${proj_home}/${pipelineSettings.outdir}` };

    params.prefix = proj.name;
    params.interleaved = projectConf.inputs.interleaved;

    if (projectConf.inputs.interleaved) {
        //inputs 
        let inputs = [];
        let input_fastq = projectConf.inputs.fastqs;
        //check upload file
        for (let i = 0; i < input_fastq.length; i++) {
            let fq = input_fastq[i];
            if (fq.startsWith(config.IO.UPLOADED_FILES_DIR)) {
                //create input dir and link uploaded file with realname
                const inputDir = proj_home + "/input";
                if (!fs.existsSync(inputDir)) {
                    fs.mkdirSync(inputDir);
                }
                const fileCode = path.basename(fq);
                let name = await common.getRealName(fileCode);
                const inputFq = inputDir + "/" + name;
                if (!fs.existsSync(inputFq)) {
                    fs.symlinkSync(fq, inputFq, 'file');
                }
                inputs.push(inputFq);
            } else {
                inputs.push(fq);
            }
        }
        params.input_files = inputs;
        params.input_fq1 = [];
        params.input_fq2 = [];
    } else {
        //inputs 
        let inputs_fq1 = [];
        let inputs_fq2 = [];
        let input_fastq = projectConf.inputs.fastqs;
        //check upload file
        for (let i = 0; i < input_fastq.length; i++) {
            let fq1 = input_fastq[i].fq1;
            if (fq1.startsWith(config.IO.UPLOADED_FILES_DIR)) {
                //create input dir and link uploaded file with realname
                const inputDir = proj_home + "/input";
                if (!fs.existsSync(inputDir)) {
                    fs.mkdirSync(inputDir);
                }
                const fileCode = path.basename(fq1);
                let name = await common.getRealName(fileCode);
                const inputFq = inputDir + "/" + name;
                fs.symlinkSync(fq1, inputFq, 'file');
                inputs_fq1.push(inputFq);
            } else {
                inputs_fq1.push(fq1);
            }
            let fq2 = input_fastq[i].fq2;
            if (fq2.startsWith(config.IO.UPLOADED_FILES_DIR)) {
                //create input dir and link uploaded file with realname
                const inputDir = proj_home + "/input";
                if (!fs.existsSync(inputDir)) {
                    fs.mkdirSync(inputDir);
                }
                const fileCode = path.basename(fq2);
                let name = await common.getRealName(fileCode);
                const inputFq = inputDir + "/" + name;
                fs.symlinkSync(fq2, inputFq, 'file');
                inputs_fq2.push(inputFq);
            } else {
                inputs_fq2.push(fq2);
            }
        }
        params.input_files = [];
        params.input_fq1 = inputs_fq1;
        params.input_fq2 = inputs_fq2;
    }

    //workflow specific inputs
    projectConf.workflows.forEach(workflow => {
        const workflowSettings = workflowlist[workflow.name];
        if (workflow.name === 'ReadsQC') {
            params.DoReadsQC = workflow.paramsOn;
            params.readsQC_outdir = proj_home + "/" + workflowSettings['outdir'];
        } else if (workflow.name === 'ReadbasedAnalysis') {
            params.DoReadbasedAnalysis = workflow.paramsOn;
            params.readbasedAnalysis_outdir = proj_home + "/" + workflowSettings['outdir'];
        } else if (workflow.name === 'MetaAssembly') {
            params.DoMetaAssembly = workflow.paramsOn;
            params.metaAssembly_outdir = proj_home + "/" + workflowSettings['outdir'];
        } else if (workflow.name === 'virus_plasmid') {
            params.DoVirusPlasmid = workflow.paramsOn;
            params.virusPlasmid_outdir = proj_home + "/" + workflowSettings['outdir'];
        } else if (workflow.name === 'MetaAnnotation') {
            params.DoAnnotation = workflow.paramsOn;
            params.metaAnnotation_outdir = proj_home + "/" + workflowSettings['outdir'];
        } else if (workflow.name === 'MetaMAGs') {
            params.DoMetaMAGs = workflow.paramsOn;
            params.metaMAGs_outdir = proj_home + "/" + workflowSettings['outdir'];
            params.input_map = workflow.input_map;
            params.input_domain = workflow.input_domain;
        }
    });

    // render input template and write to pipeline_inputs.json
    const inputs = ejs.render(template, params);
    fs.writeFileSync(`${proj_home}/pipeline_inputs.json`, inputs);
    // render options template and write to pipeline_options.json
    const options_tmpl = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelineSettings['options_tmpl'] ? pipelineSettings['options_tmpl'] : 'notfound');
    if (fs.existsSync(options_tmpl)) {
        const optionsTemplate = String(fs.readFileSync(options_tmpl));
        const options = ejs.render(optionsTemplate, params);
        fs.writeFileSync(`${proj_home}/pipeline_options.json`, options);
    }
    return true;
}