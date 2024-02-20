const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const { workflowlist, pipelinelist } = require("../config/workflow");
const common = require("../util/common");
const logger = require('../util/logger');
const { submitWorkflow, findInputsize } = require("../util/workflow");

module.exports = function pipelineMonitor() {
    logger.debug("pipeline monitor");
    //only process one job at each time based on job updated time
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] } }).sort({ updated: 1 }).then(jobs => {
        if (jobs.length >= process.env.MAX_CROMWELL_JOBS) {
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
            const proj_home = process.env.PROJECT_HOME + "/" + proj.code;
            const conf_file = proj_home + "/conf.json";
            let rawdata = fs.readFileSync(conf_file);
            let conf = JSON.parse(rawdata);

            //check input size
            let inputsize = await findInputsize(conf);
            if (inputsize > process.env.MAX_CROMWELL_JOBS_INPUTSIZE) {
                logger.debug("Project " + proj.code + " input fastq size exceeded the limit.");
                //fail project
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "input fastq size exceeded the limit.");
                return;
            }
            if ((jobInputsize + inputsize) > process.env.MAX_CROMWELL_JOBS_INPUTSIZE) {
                logger.debug("Cromwell is busy.");
                return;
            }

            logger.info("Processing pipeline request: " + proj.code);

            //set project status to 'processing'
            proj.status = "processing";
            proj.updated = Date.now();
            proj.save().then(proj => {
                common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "Generate WDL and inputs json");
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

                Promise.all([promise1, promise2]).then(function (projs) {
                    //submit workflow to cromwell
                    common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "submit workflow to cromwell");
                    logger.info("submit workflow to cromwell");
                    submitWorkflow(proj, pipeline, inputsize);
                }).catch(function (err) {
                    throw new Error("Failed to submit workflow to cromwell");
                });
            }).catch(err => {
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", err);
                logger.error(err);
            });
        });

    });
};

function generateWDL(proj_home, pipeline) {
    //build wdl
    const pipelineSettings = pipelinelist[pipeline];
    const tmpl = process.env.WORKFLOW_TEMPLATE_HOME + "/" + pipelineSettings['wdl_tmpl'];
    let templWDL = String(fs.readFileSync(tmpl));
    //write to pipeline.wdl
    fs.writeFileSync(proj_home + '/pipeline.wdl', templWDL);
    //options json
    const json = process.env.WORKFLOW_TEMPLATE_HOME + "/" + pipelineSettings['options_json'];
    let templJSON = String(fs.readFileSync(json));
    templJSON = templJSON.replace(/<OUTDIR>/, proj_home + "/" + pipelineSettings['outdir']);
    //write to options.json
    fs.writeFileSync(proj_home + '/options.json', templJSON);

    return true;
}

async function generateInputs(proj_home, conf, proj) {
    //build pipeline_inputs.json
    let pipelineInputs = "{\n";

    const pipelineSettings = pipelinelist[conf.pipeline];
    const tmpl = process.env.WORKFLOW_TEMPLATE_HOME + "/" + pipelineSettings['inputs_tmpl'];
    let templInputs = String(fs.readFileSync(tmpl));

    templInputs = templInputs.replace(/<PREFIX>/g, '"' + proj.name + '"');
    templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + pipelineSettings['outdir'] + '"');
    templInputs = templInputs.replace(/<INTERLEAVED>/, conf.inputs.interleaved);
    if (conf.inputs.interleaved) {
        //inputs 
        let inputs = [];
        let input_fastq = conf.inputs.fastqs;
        //check upload file
        for (let i = 0; i < input_fastq.length; i++) {
            let fq = input_fastq[i];
            if (fq.startsWith(process.env.FILEUPLOAD_FILE_DIR)) {
                //create input dir and link uploaded file with realname
                const inputDir = proj_home + "/input";
                if (!fs.existsSync(inputDir)) {
                    fs.mkdirSync(inputDir);
                }
                const fileCode = path.basename(fq);
                let name = await common.getRealName(fileCode);
                const inputFq = inputDir + "/" + name;
                if(!fs.existsSync(inputFq)) {
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
            if (fq1.startsWith(process.env.FILEUPLOAD_FILE_DIR)) {
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
            if (fq2.startsWith(process.env.FILEUPLOAD_FILE_DIR)) {
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
        } else if (workflow.name === 'MetaAnnotation') {
            templInputs = templInputs.replace(/<DOANNOTATION>/, workflow.paramsOn);
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
