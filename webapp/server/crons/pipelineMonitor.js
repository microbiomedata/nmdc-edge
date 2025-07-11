const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
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
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] } }).sort({ updated: 1 }).then(async jobs => {
        if (jobs.length >= config.CROMWELL.NUM_JOBS_MAX) {
            return;
        }
        //get current running/submitted projects' input size
        let jobInputsize = 0;
        jobs.forEach(job => {
            jobInputsize += job.inputsize;
        });
        //limit the running jobs the current project owner has
        const excludedUsers = await common.getUsersWithMaxRunningJobs();
        const owners = common.getValuesForKey(excludedUsers, "owner");

        //only process one request at each time
        Project.find({ 'type': 'Metagenome Pipeline', 'owner':{$nin: owners}, 'status': 'in queue' }).sort({ updated: 1 }).then(async projs => {
            let proj = projs[0];
            if (!proj) {
                logger.debug("No pipeline request to process");
                return;
            }
            //parse conf.json 
            const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
            const conf_file = proj_home + "/conf.json";
            let rawdata = fs.readFileSync(conf_file);
            let conf = JSON.parse(rawdata);

            //check input size
            let inputsize = await findInputsize(conf);
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
                const pipeline = conf.pipeline;
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
                    generateInputs(proj_home, conf, proj).then(inputs => {
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
                let promise3 = new Promise(function (resolve, reject) {
                    const options = generateOptions(proj_home, pipeline);
                    if (options) {
                        resolve(proj);
                    } else {
                        logger.error("Failed to generate options.json for project " + proj.code);
                        reject("Failed to generate options.json for project " + proj.code);
                    }
                });

                Promise.all([promise1, promise2, promise3]).then(function (projs) {
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

function generateOptions(proj_home, pipeline) {
    const pipelineSettings = pipelinelist[pipeline];
    const tmpl = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelineSettings['options_json']);
    let templInputs = String(fs.readFileSync(tmpl));
    fs.writeFileSync(proj_home + '/options.json', templInputs);
    return true;

}

function generateWDL(proj_home, pipeline) {
    //build wdl
    const pipelineSettings = pipelinelist[pipeline];
    const tmpl = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelineSettings['wdl_tmpl']);
    let templWDL = String(fs.readFileSync(tmpl));
    templWDL = templWDL.replace(/<READSQC_WDL>/g, workflowlist['ReadsQC']['wdl']);
    templWDL = templWDL.replace(/<READBASEDANALYSIS_WDL>/g, workflowlist['ReadbasedAnalysis']['wdl']);
    templWDL = templWDL.replace(/<ANNOTATION_WDL>/g, workflowlist['MetaAnnotation']['wdl']);
    templWDL = templWDL.replace(/<MAGS_WDL>/g, workflowlist['MetaMAGs']['wdl']);
    templWDL = templWDL.replace(/<ASSEMBLY_WDL>/g, workflowlist['MetaAssembly']['wdl']);
    //write to pipeline.wdl
    fs.writeFileSync(proj_home + '/pipeline.wdl', templWDL);
    return true;
}

async function generateInputs(proj_home, conf, proj) {
    //build pipeline_inputs.json
    let pipelineInputs = "{\n";

    const pipelineSettings = pipelinelist[conf.pipeline];
    const tmpl = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelineSettings['inputs_tmpl']);
    let templInputs = String(fs.readFileSync(tmpl));

    templInputs = templInputs.replace(/<PREFIX>/g, '"' + proj.name + '"');
    templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + pipelineSettings['outdir'] + '"');
    templInputs = templInputs.replace(/<INTERLEAVED>/, conf.inputs.interleaved);
    templInputs = templInputs.replace(/<SHORT_READ>/, conf.inputs.shortRead);
    if (conf.inputs.interleaved) {
        //inputs 
        let inputs = [];
        let input_fastq = conf.inputs.fastqs;
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
                if (!common.fileExistsSync(inputFq)) {
                    fs.symlinkSync(fq, inputFq, 'file');
                }
                inputs.push(inputFq);
            } else {
                inputs.push(fq);
            }
        }
        templInputs = templInputs.replace(/<INPUT_FILES>/, JSON.stringify(inputs));
        templInputs = templInputs.replace(/<INPUT_FQ1>/, '[]');
        templInputs = templInputs.replace(/<INPUT_FQ2>/, '[]');
    } else {
        //inputs 
        let inputs_fq1 = [];
        let inputs_fq2 = [];
        let input_fastq = conf.inputs.fastqs;
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
                if (!common.fileExistsSync(inputFq)) {
                    fs.symlinkSync(fq1, inputFq, 'file');
                }
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
                if (!common.fileExistsSync(inputFq)) {
                    fs.symlinkSync(fq2, inputFq, 'file');
                }
                inputs_fq2.push(inputFq);
            } else {
                inputs_fq2.push(fq2);
            }
        }
        templInputs = templInputs.replace(/<INPUT_FQ1>/, JSON.stringify(inputs_fq1));
        templInputs = templInputs.replace(/<INPUT_FQ2>/, JSON.stringify(inputs_fq2));
        templInputs = templInputs.replace(/<INPUT_FILES>/, '[]');
    }

    //workflow specific inputs
    conf.workflows.forEach(workflow => {
        const workflowSettings = workflowlist[workflow.name];
        if (workflow.name === 'ReadsQC') {
            templInputs = templInputs.replace(/<DOREADSQC>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<READSQC_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        } else if (workflow.name === 'ReadbasedAnalysis') {
            templInputs = templInputs.replace(/<DOREADBASEDANALYSIS>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<RBA_ENABLED_TOOLS>/, JSON.stringify(workflow['enabled_tools']));
            templInputs = templInputs.replace(/<READBASEDANALYSIS_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        } else if (workflow.name === 'MetaAssembly') {
            templInputs = templInputs.replace(/<DOMETAASSEMBLY>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<METAASSEMBLY_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        } else if (workflow.name === 'virus_plasmid') {
            templInputs = templInputs.replace(/<DOVIRUSPLASMID>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<VIRUSPLASMID_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        } else if (workflow.name === 'MetaAnnotation') {
            templInputs = templInputs.replace(/<DOANNOTATION>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<OPAVER_WEB_DIR>/,  '"' + config.IO.OPAVER_WEB_DIR + '"');
            templInputs = templInputs.replace(/<METAANNOTATION_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        } else if (workflow.name === 'MetaMAGs') {
            templInputs = templInputs.replace(/<DOMETAMAGS>/, workflow.paramsOn);
            templInputs = templInputs.replace(/<METAMAGS_OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
            if (workflow.input_map) {
                templInputs = templInputs.replace(/<METAMAGS_MAP_FILE>/, workflow.input_map);
            } else {
                templInputs = templInputs.replace(/<METAMAGS_MAP_FILE>/, 'null');
            }
            if (workflow.input_domain) {
                templInputs = templInputs.replace(/<METAMAGS_DOMAIN_FILE>/, workflow.input_domain);
            } else {
                templInputs = templInputs.replace(/<METAMAGS_DOMAIN_FILE>/, 'null');
            }
        }
    });

    pipelineInputs += templInputs + "\n";
    pipelineInputs += "}\n";
    //write to pipeline_inputs.json
    fs.writeFileSync(proj_home + '/pipeline_inputs.json', pipelineInputs);
    return true;
}
