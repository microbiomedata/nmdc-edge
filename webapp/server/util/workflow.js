const fs = require('fs');
const ejs = require('ejs');
const path = require("path");
const ufs = require("url-file-size");
const moment = require('moment');
const FormData = require('form-data');
const Papa = require('papaparse');
const CromwellJob = require("../models/CromwellJob");
const { workflowlist, pipelinelist } = require("../config/workflow");
const common = require("./common");
const logger = require('./logger');
const config = require("../config");

function generateWDL(proj_home, workflow) {
    const workflowSettings = workflowlist[workflow.name];
    //without wdl template
    const main_wdl = path.join(config.WORKFLOWS.WDL_DIR, workflowSettings['main_wdl'] ? workflowSettings['main_wdl'] : "notfound");
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
    // workflowlist: config/workflow.js
    // commonConf: data/workflow/templates/common.json
    const workflowName = projectConf.workflow.name;
    const workflowSettings = workflowlist[workflowName];
    const commonConf = JSON.parse(fs.readFileSync(config.WORKFLOWS.COMMON));
    const tmpl_inputs = path.join(config.WORKFLOWS.TEMPLATE_DIR, workflowSettings['inputs_tmpl'] ? workflowSettings['inputs_tmpl'] : "notfound");
    if (!fs.existsSync(tmpl_inputs)) {
        logger.error("workflow inputs template not found: " + tmpl_inputs);
        return false;
    }
    const template = String(fs.readFileSync(tmpl_inputs));
    const params = { ...commonConf, ...projectConf.workflow, outdir: `${proj_home}/${workflowSettings.outdir}` };

    params.prefix = proj.name;
    params.project_name = proj.name;
    if (workflowName === 'sra2fastq') {
        //use shared directory
        params.outdir = config.IO.SRA_BASE_DIR;
        //accessions string to arrray
        const accessions = projectConf.workflow['accessions'].toUpperCase().split(/\s*(?:,|$)\s*/);
        //filter out accessions already exist in sra data home
        const accessions4workflow = accessions.filter(
            accession => !fs.existsSync(config.IO.SRA_BASE_DIR + "/" + accession)
        );
        params.accessions = accessions4workflow;
    } else if (workflowName === 'ReadsQC' || workflowName === 'MetaAssembly' || workflowName === 'Metatranscriptome') {
        let interleaved = projectConf.workflow['input_fastq']['interleaved'];
        let input_fastq = projectConf.workflow['input_fastq']['fastqs'];
        params.interleaved = interleaved;
        if (interleaved) {
            //inputs 
            let inputs_fq = [];
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
                    let linkFq = inputDir + "/" + name;
                    let i = 1;
                    while (fs.existsSync(linkFq)) {
                        i++;
                        if (name.includes(".")) {
                            let newName = name.replace(".", i + ".");
                            linkFq = inputDir + "/" + newName;
                        } else {
                            linkFq = inputDir + "/" + name + i;
                        }
                    }
                    fs.symlinkSync(fq, linkFq, 'file');
                    inputs_fq.push(linkFq);
                } else {
                    inputs_fq.push(fq);
                }
            }

            if (workflowName === 'Metatranscriptome') {
                params.input_file = inputs_fq[0];
                params.input_fq1 = "";
                params.input_fq2 = "";
            } else {
                params.input_files = inputs_fq;
                params.input_fq1 = [];
                params.input_fq2 = [];
            }
        } else {
            //inputs 
            let inputs_fq1 = [];
            let inputs_fq2 = [];
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
                    let linkFq = inputDir + "/" + name;
                    let i = 1;
                    while (fs.existsSync(linkFq)) {
                        i++;
                        if (name.includes(".")) {
                            let newName = name.replace(".", i + ".");
                            linkFq = inputDir + "/" + newName;
                        } else {
                            linkFq = inputDir + "/" + name + i;
                        }
                    }
                    fs.symlinkSync(fq1, linkFq, 'file');
                    inputs_fq1.push(linkFq);
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
                    let linkFq = inputDir + "/" + name;
                    let i = 1;
                    while (fs.existsSync(linkFq)) {
                        i++;
                        if (name.includes(".")) {
                            let newName = name.replace(".", i + ".");
                            linkFq = inputDir + "/" + newName;
                        } else {
                            linkFq = inputDir + "/" + name + i;
                        }
                    }
                    fs.symlinkSync(fq2, linkFq, 'file');
                    inputs_fq2.push(linkFq);
                } else {
                    inputs_fq2.push(fq2);
                }
            }
            if (workflowName === 'Metatranscriptome') {
                params.input_file = "";
                params.input_fq1 = inputs_fq1[0];
                params.input_fq2 = inputs_fq2[0];
            } else {
                params.input_files = [];
                params.input_fq1 = inputs_fq1;
                params.input_fq2 = inputs_fq2;
            }
        }
    }

    // render input template and write to pipeline_inputs.json
    const inputs = ejs.render(template, params);
    fs.writeFileSync(`${proj_home}/pipeline_inputs.json`, inputs);
    // render options template and write to pipeline_options.json
    const options_tmpl = path.join(config.WORKFLOWS.TEMPLATE_DIR, workflowlist[workflowName]['options_tmpl'] ? workflowlist[workflowName]['options_tmpl'] : 'notfound');
    if (fs.existsSync(options_tmpl)) {
        const optionsTemplate = String(fs.readFileSync(options_tmpl));
        const options = ejs.render(optionsTemplate, params);
        fs.writeFileSync(`${proj_home}/pipeline_options.json`, options);
    }
    return true;
}

//submit workflow to cromwell through api
function submitWorkflow(proj, workflow, inputsize) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
    let formData = new FormData();
    formData.append("workflowSource", fs.createReadStream(proj_home + '/pipeline.wdl'));
    logger.debug("workflowSource: " + proj_home + '/pipeline.wdl');
    formData.append("workflowInputs", fs.createReadStream(proj_home + '/pipeline_inputs.json'));
    logger.debug("workflowInputs: " + proj_home + '/pipeline_inputs.json');

    //imports.wdl
    let imports = path.join(config.WORKFLOWS.WDL_DIR, "imports.zip");
    let wdlVersion = config.CROMWELL.WORKFLOW_TYPE_VERSION;
    //options_json
    if (workflow) {
        let options_json = proj_home + '/pipeline_options.json';
        if (workflow.name) {
            imports = path.join(config.WORKFLOWS.WDL_DIR, workflowlist[workflow.name]['wdl_imports']);
            wdlVersion = workflowlist[workflow.name]['wdl_version'];
        } else {
            imports = path.join(config.WORKFLOWS.WDL_DIR, pipelinelist[workflow]['wdl_imports']);
            wdlVersion = pipelinelist[workflow]['wdl_version'];
        }
        if (fs.existsSync(options_json)) {
            formData.append("workflowOptions", fs.createReadStream(options_json));
            logger.debug("workflowOptions: " + options_json);
        }
    }

    formData.append("workflowType", config.CROMWELL.WORKFLOW_TYPE);
    if (wdlVersion) {
        logger.debug("wdlVersion: " + wdlVersion)
        formData.append("workflowTypeVersion", wdlVersion);
    }
    formData.append("workflowDependencies", fs.createReadStream(imports), { contentType: 'application/zip' });
    logger.debug("workflowDependencies: " + imports);

    const formHeaders = formData.getHeaders();
    const formBoundary = formData.getBoundary();

    const url = `${config.CROMWELL.API_BASE_URL}/api/workflows/v1`;
    common.postData(url, formData, {
        headers: {
            ...formHeaders, formBoundary
        },
    }).then(response => {
        logger.debug(JSON.stringify(response))
        const newCromwellJob = new CromwellJob({
            id: response.id,
            project: proj.code,
            type: proj.type,
            inputsize: inputsize,
            status: 'Submitted'
        });
        newCromwellJob.save().catch(err => { logger.error("falied to save to cromwelljobs: ", err) });
        proj.status = 'submitted';
        proj.updated = Date.now();
        proj.save();
    }).catch(error => {
        proj.status = 'failed';
        proj.updated = Date.now();
        proj.save();
        let message = error;
        if (error.data) {
            message = error.data.message;
        }
        common.write2log(path.join(config.PROJECTS.BASE_DIR, proj.code, "log.txt"), message);
        logger.error("Failed to submit workflow to Cromwell: " + message);
    });
}

const generateWorkflowResult = function (proj) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
    const result_json = proj_home + "/result.json";

    if (!fs.existsSync(result_json)) {
        let result = {};
        const conf_file = proj_home + "/conf.json";
        let rawdata = fs.readFileSync(conf_file);
        let workflowConf = JSON.parse(rawdata);
        const outdir = proj_home + '/' + workflowlist[workflowConf.workflow.name].outdir;

        if (workflowConf.workflow.name === 'ReadsQC') {
            let stats = {};
            const dirs = fs.readdirSync(outdir);
            dirs.forEach(function (dir) {
                if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                    //load filterStats.json
                    stats[dir] = JSON.parse(fs.readFileSync(outdir + "/" + dir + "/filterStats.json"));
                }
            });
            result['stats'] = stats;
        } else if (workflowConf.workflow.name === 'MetaAssembly') {
            let statsOut = outdir + "/final_assembly/stats.json";
            if (!fs.existsSync(statsOut)) {
                statsOut = outdir + "/stats.json";
            }
            result['stats'] = JSON.parse(fs.readFileSync(statsOut));

        } else if (workflowConf.workflow.name === 'ReadbasedAnalysis') {
            let summary = null;
            let htmls = {};
            const dirs = fs.readdirSync(outdir);
            dirs.forEach(function (dir) {
                if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                    //get html
                    const subs = fs.readdirSync(outdir + "/" + dir).filter(file => {
                        return file.endsWith('html');
                    });
                    let subHtmls = []
                    subs.forEach(function (html) {
                        subHtmls.push(workflowlist[workflowConf.workflow.name].outdir + "/" + dir + "/" + html);
                    });
                    htmls[dir] = { "htmls": subHtmls };
                } else if (dir.endsWith(".json") && dir !== 'activity.json' && dir !== 'data_objects.json') {
                    summary = JSON.parse(fs.readFileSync(outdir + "/" + dir));
                }
            });
            result = { "html": htmls, "summary": summary };

        } else if (workflowConf.workflow.name === 'MetaAnnotation') {
            //find <prefix>_structural_annotation_stats.json
            const files = fs.readdirSync(outdir);
            files.forEach(function (file) {
                if (file.endsWith("_structural_annotation_stats.json")) {
                    result['stats'] = JSON.parse(fs.readFileSync(outdir + "/" + file));
                }
            });

        } else if (workflowConf.workflow.name === 'MetaMAGs') {
            //result['stats'] = JSON.parse(fs.readFileSync(outdir + "/MAGs_stats.json"));

            let stats = JSON.parse(fs.readFileSync(outdir + "/MAGs_stats.json"));
            Object.keys(stats).forEach((item, index) => {
                //mags_list
                if (typeof stats[item] === 'object') {
                    //delete members_id
                    for (var i = 0; i < stats[item].length; i++) {
                        delete stats[item][i]['members_id'];
                    }
                }
            });
            result['stats'] = stats;
        } else if (workflowConf.workflow.name === 'Metatranscriptome') {
            result['top_features'] = JSON.parse(fs.readFileSync(outdir + "/metat_output/top100_features.json"));
            const features_tsv = outdir + "/metat_output/rpkm_sorted_features.tsv";
            if (fs.existsSync(features_tsv)) {
                result['features_tsv'] = "output/Metatranscriptome/metat_output/rpkm_sorted_features.tsv";
            }
        } else if (workflowConf.workflow.name === 'EnviroMS') {
            let stats = {};
            const dirs = fs.readdirSync(outdir);
            dirs.forEach(function (dir) {
                if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                    stats[dir] = {};
                    //load <input filename>.json
                    const subs = fs.readdirSync(outdir + "/" + dir).filter(file => {
                        return file.endsWith('.json');
                    });
                    stats[dir]['conf'] = JSON.parse(fs.readFileSync(outdir + "/" + dir + "/" + subs[0]));
                    //get .png
                    const pngs = fs.readdirSync(outdir + "/" + dir).filter(file => {
                        return file.endsWith('.png');
                    });
                    stats[dir]['pngs'] = {};
                    pngs.forEach(function (png) {
                        stats[dir]['pngs'][png] = workflowlist[workflowConf.workflow.name].outdir + "/" + dir + "/" + png;
                    });
                    //get molecules
                    let top_molecules = outdir + "/" + dir + "/top100_molecules.json";
                    if (fs.existsSync(top_molecules))
                        stats[dir]['top_molecules'] = JSON.parse(fs.readFileSync(top_molecules));
                    const molecules_tsv = outdir + "/" + dir + "/enviroms_sorted_molecules.tsv";
                    if (fs.existsSync(molecules_tsv)) {
                        stats[dir]['molecules_tsv'] = "output/EnviroMS/" + dir + "/enviroms_sorted_molecules.tsv";
                    }
                }
            });
            result['stats'] = stats;
            logger.debug(result)
        } else if (workflowConf.workflow.name === 'virus_plasmid') {
            const dirs = fs.readdirSync(outdir);
            dirs.forEach(function (dir) {
                if (fs.statSync(outdir + "/" + dir).isDirectory() && dir.endsWith('summary')) {
                    const summaryFiles = fs.readdirSync(outdir + "/" + dir);
                    summaryFiles.forEach(function (summaryFile) {
                        if (summaryFile.endsWith('plasmid_summary.tsv')) {
                            result['plasmid_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                        }
                        if (summaryFile.endsWith('virus_summary.tsv')) {
                            result['virus_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                        }
                    });
                }
                if (fs.statSync(outdir + "/" + dir).isDirectory() && dir.endsWith('checkv')) {
                    const summaryFiles = fs.readdirSync(outdir + "/" + dir);
                    summaryFiles.forEach(function (summaryFile) {
                        if (summaryFile.endsWith('quality_summary.tsv')) {
                            result['quality_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                        }
                    });
                }
            });
        } else if (workflowConf.workflow.name === 'Metaproteomics') {
            const dirs = fs.readdirSync(outdir);
            dirs.forEach(function (summaryFile) {
                if (summaryFile.endsWith('_QC_metrics.tsv')) {
                    result['quality_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                }
            });
        } else if (workflowConf.workflow.name === 'sra2fastq') {
            //use relative path 
            //const sraDataDir = config.IO.SRA_DATA_BASE_DIR;
            const accessions = workflowConf.workflow.accessions.toUpperCase().split(/\s*(?:,|$)\s*/);;
            accessions.forEach((accession) => {
                // link sra downloads to project output
                fs.symlinkSync("../../../../sra/" + accession, outdir + "/" + accession)

            })
        }

        fs.writeFileSync(result_json, JSON.stringify(result));
    }
}

const generatePipelineResult = function (proj) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
    const result_json = proj_home + "/result.json";

    if (!fs.existsSync(result_json)) {
        let result = {};
        const conf_file = proj_home + "/conf.json";
        let rawdata = fs.readFileSync(conf_file);
        let pipelineConf = JSON.parse(rawdata);
        result['workflows'] = pipelineConf.workflows;

        pipelineConf.workflows.forEach(workflow => {
            const outdir = proj_home + '/' + workflowlist[workflow.name].outdir;
            if (workflow.name === 'ReadsQC' && workflow.paramsOn) {
                result[workflow.name] = {};
                let stats = {};
                if (fs.existsSync(outdir)) {
                    const dirs = fs.readdirSync(outdir);
                    dirs.forEach(function (dir) {
                        if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                            //load filterStats.json
                            stats[dir] = JSON.parse(fs.readFileSync(outdir + "/" + dir + "/filterStats.json"));
                        }
                    });
                }
                result[workflow.name]['stats'] = stats;
            } else if (workflow.name === 'MetaAssembly' && workflow.paramsOn) {
                result[workflow.name] = {};
                let statsOut = outdir + "/final_assembly/stats.json";
                if (!fs.existsSync(statsOut)) {
                    statsOut = outdir + "/stats.json";
                }
                if (fs.existsSync(statsOut)) {
                    result[workflow.name]['stats'] = JSON.parse(fs.readFileSync(statsOut));
                }

            } else if (workflow.name === 'ReadbasedAnalysis' && workflow.paramsOn) {
                result[workflow.name] = {};
                let summary = null;
                let htmls = {};
                if (fs.existsSync(outdir)) {
                    const dirs = fs.readdirSync(outdir);
                    dirs.forEach(function (dir) {
                        if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                            //get html
                            const subs = fs.readdirSync(outdir + "/" + dir).filter(file => {
                                return file.endsWith('html');
                            });
                            let subHtmls = []
                            subs.forEach(function (html) {
                                subHtmls.push(workflowlist[workflow.name].outdir + "/" + dir + "/" + html);
                            });
                            htmls[dir] = { "htmls": subHtmls };
                        } else if (dir.endsWith(".json") && dir !== 'activity.json' && dir !== 'data_objects.json') {
                            summary = JSON.parse(fs.readFileSync(outdir + "/" + dir));
                        }
                    });
                }
                result[workflow.name] = { "html": htmls, "summary": summary };

            } else if (workflow.name === 'MetaAnnotation' && workflow.paramsOn) {
                result[workflow.name] = {};
                //find <prefix>_structural_annotation_stats.json
                if (fs.existsSync(outdir)) {
                    const files = fs.readdirSync(outdir);
                    files.forEach(function (file) {
                        if (file.endsWith("_structural_annotation_stats.json")) {
                            result[workflow.name]['stats'] = JSON.parse(fs.readFileSync(outdir + "/" + file));
                        }
                    });
                }

            } else if (workflow.name === 'MetaMAGs' && workflow.paramsOn) {
                result[workflow.name] = {};
                if (fs.existsSync(outdir + "/MAGs_stats.json")) {

                    let stats = JSON.parse(fs.readFileSync(outdir + "/MAGs_stats.json"));
                    Object.keys(stats).forEach((item, index) => {
                        //mags_list
                        if (typeof stats[item] === 'object') {
                            //delete members_id
                            for (var i = 0; i < stats[item].length; i++) {
                                delete stats[item][i]['members_id'];
                            }
                        }
                    });
                    result[workflow.name]['stats'] = stats;
                }
            }
        });

        fs.writeFileSync(result_json, JSON.stringify(result));
    }
}


function generateRunStats(project) {
    let conf_file = path.join(config.PROJECTS.BASE_DIR, project.code, 'conf.json');
    let job_metadata_file = path.join(config.PROJECTS.BASE_DIR, project.code, 'cromwell_job_metadata.json');

    let rawdata = fs.readFileSync(conf_file);
    let conf = JSON.parse(rawdata);

    let stats = [];
    if (fs.existsSync(job_metadata_file)) {
        rawdata = fs.readFileSync(job_metadata_file);
        let jobStats = JSON.parse(rawdata);
        if (conf.workflow) {
            let workflowStats = {};
            const cromwellCalls = workflowlist[conf.workflow.name]["cromwell_calls"];
            workflowStats['Workflow'] = workflowlist[conf.workflow.name].full_name;
            workflowStats['Run'] = 'On';
            getWorkflowStats(jobStats, cromwellCalls, conf.workflow, workflowStats, stats);
        }
        if (conf.workflows) {
            conf.workflows.forEach(workflow => {
                let workflowStats = {};
                let cromwellCalls = pipelinelist[conf.pipeline]["workflows"][workflow.name]["cromwell_calls"];
                workflowStats['Workflow'] = pipelinelist[conf.pipeline]["workflows"][workflow.name].full_name;
                if (workflow.paramsOn) {
                    workflowStats['Run'] = 'On';
                } else {
                    workflowStats['Run'] = 'Off';
                }

                getWorkflowStats(jobStats, cromwellCalls, workflow, workflowStats, stats);
            });
        }
    }

    fs.writeFileSync(path.join(config.PROJECTS.BASE_DIR, project.code, 'run_stats.json'), JSON.stringify({ 'stats': stats }));
}

function getWorkflowStats(jobStats, cromwellCalls, workflow, workflowStats, stats) {
    workflowStats['Status'] = '';
    workflowStats['Running Time'] = '';
    workflowStats['Start'] = '';
    workflowStats['End'] = '';
    let myStart = '';
    let myEnd = '';
    cromwellCalls.forEach(cromwellCall => {
        if (jobStats['calls'][cromwellCall]) {
            if (!workflowStats['Status'] || workflowStats['Status'] !== 'Failed') {
                //set status to 'Failed' is one of the subjob is failed
                workflowStats['Status'] = jobStats['calls'][cromwellCall][0]['executionStatus'];
            }
            let start = jobStats['calls'][cromwellCall][0]['start'];
            let end = jobStats['calls'][cromwellCall][0]['end'];

            if (start && !workflowStats['Start']) {
                workflowStats['Start'] = moment(start).format('YYYY-MM-DD HH:mm:ss');
                myStart = start;
            }
            if (end) {
                workflowStats['End'] = moment(end).format('YYYY-MM-DD HH:mm:ss');
                myEnd = end;
            }
        }
    });

    if (myStart && myEnd) {
        var ms = moment(myEnd, 'YYYY-MM-DD HH:mm:ss').diff(moment(myStart, 'YYYY-MM-DD HH:mm:ss'));
        var d = moment.duration(ms);
        workflowStats['Running Time'] = timeFormat(d);
    }
    stats.push(workflowStats);

    if (workflowStats['Workflow'] === 'Read-based Taxonomy Classification' && workflowStats['Run'] === 'On') {
        let tools = workflow.enabled_tools;

        Object.keys(tools).map((tool, index) => {
            let toolStats = {};
            toolStats['Workflow'] = '-- ' + tool;
            if (tools[tool]) {
                toolStats['Run'] = '';
                toolStats['Status'] = '';
                toolStats['Running Time'] = '';
                toolStats['Start'] = '';
                toolStats['End'] = '';
                stats.push(toolStats);
            }
        });
    }
}

function timeFormat(d) {
    var hours = d.days() * 24 + d.hours();
    if (hours < 10) {
        hours = '0' + hours;
    }
    var minutes = d.minutes();
    if (minutes < 10) {
        minutes = '0' + minutes;
    }
    var seconds = d.seconds();
    if (seconds < 10) {
        seconds = '0' + seconds;
    }
    return hours + ':' + minutes + ':' + seconds;
}

async function findInputsize(conf) {
    let size = 0;
    const pipeline = conf.pipeline;
    if (pipeline === 'Metagenome Pipeline') {
        const fastqs = conf.inputs.fastqs;
        if (conf.inputs.interleaved) {
            await Promise.all(fastqs.map(async (file) => {
                let stats = await fileStats(file);
                size += stats.size;

            }));
        } else {
            await Promise.all(fastqs.map(async (paired) => {
                let stats = await fileStats(paired.fq1);
                size += stats.size;
                stats = await fileStats(paired.fq2);
                size += stats.size;
            }));
        }

    } else {
        const workflow = conf.workflow.name;
        if (workflow === 'ReadsQC' || workflow === 'MetaAssembly' || workflow === 'Metatranscriptome') {
            const fastqs = conf.workflow.input_fastq.fastqs;
            if (conf.workflow.input_fastq.interleaved) {
                await Promise.all(fastqs.map(async (file) => {
                    let stats = await fileStats(file);
                    size += stats.size;
                }));
            } else {
                await Promise.all(fastqs.map(async (paired) => {
                    let stats = await fileStats(paired.fq1);
                    size += stats.size;
                    stats = await fileStats(paired.fq2);
                    size += stats.size;
                }));
            }
        }
        else if (workflow === 'ReadbasedAnalysis') {
            const fastqs = conf.workflow.reads;
            await Promise.all(fastqs.map(async (file) => {
                let stats = await fileStats(file);
                size += stats.size;
            }));
        }
        else if (workflow === 'MetaAnnotation') {
            let stats = await fileStats(conf.workflow.input_fasta);
            size += stats.size;
        }
        else if (workflow === 'MetaMAGs') {
            let stats = await fileStats(conf.workflow.input_contig);
            size += stats.size;
            stats = await fileStats(conf.workflow.input_sam);
            size += stats.size;
            stats = await fileStats(conf.workflow.input_gff);
            size += stats.size;
            if (conf.workflow.input_map) {
                stats = await fileStats(conf.workflow.input_map);
                size += stats.size;
            }
        }
        else if (workflow === 'EnviroMS') {
            const ins = conf.workflow.file_paths;
            await Promise.all(ins.map(async (file) => {
                let stats = await fileStats(file);
                size += stats.size;
            }));
        }
        else if (workflow === 'virus_plasmid') {
            const file = conf.workflow.input_fasta;
            let stats = await fileStats(file);
            size += stats.size;
        }
        else if (workflow === 'Metaproteomics') {
            let stats = await fileStats(conf.workflow.input_raw);
            size += stats.size;
            stats = await fileStats(conf.workflow.input_fasta);
            size += stats.size;
            stats = await fileStats(conf.workflow.input_gff);
            size += stats.size;
        }
    }
    //console.log("file size", size)
    return size;
}

async function fileStats(file) {
    if (file.toLowerCase().startsWith('http')) {
        return await ufs(file)
            .then(size => { return { size: size } })
            .catch(err => { return { size: 0 } });
    } else {
        return fs.statSync(file);
    }
}

module.exports = { generateWDL, generateInputs, submitWorkflow, generateWorkflowResult, generatePipelineResult, generateRunStats, findInputsize };
