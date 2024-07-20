const fs = require('fs');
const path = require("path");
const execSync = require('child_process').execSync;
const ufs = require("url-file-size");
const moment = require('moment');
const FormData = require('form-data');
const Papa = require('papaparse');
const CromwellJob = require("../models/CromwellJob");
const { workflowlist, pipelinelist } = require("../config/workflow");
const common = require("./common");
const logger = require('./logger');
const config = require("../config");

//submit workflow to cromwell through api
function submitWorkflow(proj, workflow, inputsize) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, proj.code);
    let formData = new FormData();
    formData.append("workflowSource", fs.createReadStream(proj_home + '/pipeline.wdl'));
    logger.debug("workflowSource: " + proj_home + '/pipeline.wdl');
    formData.append("workflowInputs", fs.createReadStream(proj_home + '/pipeline_inputs.json'));
    logger.debug("workflowInputs" + proj_home + '/pipeline_inputs.json');
    const options_json = proj_home + '/options.json';
    if (fs.existsSync(options_json)) {
        formData.append("workflowOptions", fs.createReadStream(options_json));
        logger.debug("workflowOptions:" + options_json);
    }

    //imports.wdl
    let imports = path.join(config.WORKFLOWS.WDL_DIR, "imports.zip");
    let wdlVersion = config.CROMWELL.WORKFLOW_TYPE_VERSION;
    //options_json
    if (workflow) {
        // let options_json = null;
        if (workflow.name) {
            // options_json = path.join(config.WORKFLOWS.TEMPLATE_DIR, workflowlist[workflow.name]['options_json'] ? workflowlist[workflow.name]['options_json'] : 'notfound');
            imports = path.join(config.WORKFLOWS.WDL_DIR, workflowlist[workflow.name]['wdl_imports']);
            wdlVersion = workflowlist[workflow.name]['wdl_version'];
        } else {
            // options_json = path.join(config.WORKFLOWS.TEMPLATE_DIR, pipelinelist[workflow]['options_json'] ? pipelinelist[workflow]['options_json'] : 'notfound');
            imports = path.join(config.WORKFLOWS.WDL_DIR, pipelinelist[workflow]['wdl_imports']);
            wdlVersion = pipelinelist[workflow]['wdl_version'];
        }
    }

    formData.append("workflowType", config.CROMWELL.WORKFLOW_TYPE);
    if (wdlVersion) {
        logger.debug("wdlVersion:" + wdlVersion)
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

    let result = {};
    const conf_file = proj_home + "/conf.json";
    let rawdata = fs.readFileSync(conf_file);
    let workflowConf = JSON.parse(rawdata);
    const outdir = proj_home + '/' + workflowlist[workflowConf.workflow.name].outdir;

    if (workflowConf.workflow.name === 'ReadsQC') {
        let stats = {};
        let summaries = {};
        const dirs = fs.readdirSync(outdir);
        dirs.forEach(function (dir) {
            if (dir === 'multiqc_report.html') {
                result['reportHtml'] = workflowlist[workflowConf.workflow.name].outdir + "/multiqc_report.html";
            }
            else if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                stats[dir] = JSON.parse(fs.readFileSync(outdir + "/" + dir + "/filterStats.json"));
                //qc_summary.html
                if (fs.existsSync(outdir + "/" + dir + "/qc_summary.html")) {
                    summaries[dir] = workflowlist[workflowConf.workflow.name].outdir + "/" + dir + "/qc_summary.html";
                }
            }
        });
        result['stats'] = stats;
        result['summaries'] = summaries;
    } else if (workflowConf.workflow.name === 'MetaAssembly') {
        let statsOut = outdir + "/final_assembly/stats.json";
        if (!fs.existsSync(statsOut)) {
            statsOut = outdir + "/stats.json";
        }
        result['stats'] = JSON.parse(fs.readFileSync(statsOut));
        let reportHtml = outdir + "/metagenome_workflow_report.html";
        if (fs.existsSync(reportHtml)) {
            result['reportHtml'] = workflowlist[workflowConf.workflow.name].outdir + "/metagenome_workflow_report.html";
        }

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
            if (file.endsWith("protein_size_histogram.html")) {
                result['proteinSizeHistogram'] = workflowlist[workflowConf.workflow.name].outdir + "/" + file;
            }
            if (file === "opaver_web_path.json") {
                const webPath = JSON.parse(fs.readFileSync(outdir + "/" + file));
                result['opaverWebPath'] = webPath['opaver_web_path'];
            }
        });

    } else if (workflowConf.workflow.name === 'MetaMAGs') {
        const files = fs.readdirSync(outdir);
        files.forEach(function (file) {
            if (file.endsWith("_mags_stats.json")) {
                let stats = JSON.parse(fs.readFileSync(outdir + "/" + file));
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
            }
            if (file.endsWith("_barplot.png")) {
                result['barplot'] = workflowlist[workflowConf.workflow.name].outdir + "/" + file;
            }
            if (file.endsWith("_heatmap.png")) {
                result['heatmap'] = workflowlist[workflowConf.workflow.name].outdir + "/" + file;
            }
            if (file.endsWith("_kronaplot.html")) {
                result['kronaplot'] = workflowlist[workflowConf.workflow.name].outdir + "/" + file;
            }
        });
    } else if (workflowConf.workflow.name === 'Metatranscriptome') {
        const dirs = fs.readdirSync(outdir);
        dirs.forEach(function (dir) {
            if (dir === 'readsQC') {
                const files = fs.readdirSync(outdir + "/readsQC");
                files.forEach(function (file) {
                    if (file.endsWith("_stats.json")) {
                        result['readsQC-stats'] = JSON.parse(fs.readFileSync(outdir + "/readsQC/" + file));
                    }
                });
            }
            else if (dir === 'assembly') {
                const files = fs.readdirSync(outdir + "/assembly");
                files.forEach(function (file) {
                    if (file === "stats.json") {
                        result['assembly-stats'] = JSON.parse(fs.readFileSync(outdir + "/assembly/" + file));
                    }
                });
            }
            else if (dir === 'annotation') {
                const files = fs.readdirSync(outdir + "/annotation");
                files.forEach(function (file) {
                    if (file.endsWith("_stats.json")) {
                        result['annotation-stats'] = JSON.parse(fs.readFileSync(outdir + "/annotation/" + file));
                    }
                });
            }
            else if (dir === 'readMapping') {
                const files = fs.readdirSync(outdir + "/readMapping");
                files.forEach(function (file) {
                    if (file.endsWith("_sorted_features.tsv")) {
                        var rows = parseInt(execSync("wc -l < " + outdir + "/readMapping/" + file).toString().trim());
                        if (rows > config.IO.MAX_DATATABLE_ROWS) {
                            result['readMapping-features-too-large'] = true;
                            result['readMapping-features'] = "output/Metatranscriptomics/readMapping/" + file;
                        } else {
                            result['readMapping-features-too-large'] = false;
                            result['readMapping-features'] = Papa.parse(fs.readFileSync(outdir + "/readMapping/" + file).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                        }
                    }
                });
            }
        });
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
                const molecules_tsv = outdir + "/" + dir + "/enviroms_sorted_molecules.tsv";
                if (fs.existsSync(molecules_tsv)) {
                    //stats[dir]['molecules_tsv'] = "output/NOM/" + dir + "/enviroms_sorted_molecules.tsv";
                    stats[dir]['molecules_json'] = Papa.parse(fs.readFileSync(molecules_tsv).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
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
        const accessions = workflowConf.workflow.accessions.toUpperCase().split(/\s*(?:,|$)\s*/);
        accessions.forEach((accession) => {
            // link sra downloads to project output
            if (!fs.existsSync(outdir + "/" + accession)) {
                fs.symlinkSync("../../../../sra/" + accession, outdir + "/" + accession);
            }

        })
    }

    fs.writeFileSync(result_json, JSON.stringify(result));

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
                let summaries = {};
                if (fs.existsSync(outdir)) {
                    const dirs = fs.readdirSync(outdir);
                    dirs.forEach(function (dir) {
                        if (dir === 'multiqc_report.html') {
                            result[workflow.name]['reportHtml'] = workflowlist[workflow.name].outdir + "/multiqc_report.html";
                        }
                        else if (fs.statSync(outdir + "/" + dir).isDirectory()) {
                            stats[dir] = JSON.parse(fs.readFileSync(outdir + "/" + dir + "/filterStats.json"));
                            //qc_summary.html
                            if (fs.existsSync(outdir + "/" + dir + "/qc_summary.html")) {
                                summaries[dir] = workflowlist[workflow.name].outdir + "/" + dir + "/qc_summary.html";
                            }
                        }
                    });
                }
                result[workflow.name]['stats'] = stats;
                result[workflow.name]['summaries'] = summaries;
            } else if (workflow.name === 'MetaAssembly' && workflow.paramsOn) {
                result[workflow.name] = {};
                let statsOut = outdir + "/final_assembly/stats.json";
                if (!fs.existsSync(statsOut)) {
                    statsOut = outdir + "/stats.json";
                }
                if (fs.existsSync(statsOut)) {
                    result[workflow.name]['stats'] = JSON.parse(fs.readFileSync(statsOut));
                }
                let reportHtml = outdir + "/metagenome_workflow_report.html";
                if (fs.existsSync(reportHtml)) {
                    result[workflow.name]['reportHtml'] = workflowlist[workflow.name].outdir + "/metagenome_workflow_report.html";
                }
                console.log(result[workflow.name]['reportHtml'])

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

            } else if (workflow.name === 'virus_plasmid' && workflow.paramsOn) {
                result[workflow.name] = {};
                if (fs.existsSync(outdir)) {
                    const dirs = fs.readdirSync(outdir);
                    dirs.forEach(function (dir) {
                        if (fs.statSync(outdir + "/" + dir).isDirectory() && dir.endsWith('summary')) {
                            const summaryFiles = fs.readdirSync(outdir + "/" + dir);
                            summaryFiles.forEach(function (summaryFile) {
                                if (summaryFile.endsWith('plasmid_summary.tsv')) {
                                    result[workflow.name]['plasmid_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                                }
                                if (summaryFile.endsWith('virus_summary.tsv')) {
                                    result[workflow.name]['virus_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                                }
                            });
                        }
                        if (fs.statSync(outdir + "/" + dir).isDirectory() && dir.endsWith('checkv')) {
                            const summaryFiles = fs.readdirSync(outdir + "/" + dir);
                            summaryFiles.forEach(function (summaryFile) {
                                if (summaryFile.endsWith('quality_summary.tsv')) {
                                    result[workflow.name]['quality_summary'] = Papa.parse(fs.readFileSync(outdir + "/" + dir + "/" + summaryFile).toString(), { delimiter: '\t', header: true, skipEmptyLines: true }).data;
                                }
                            });
                        }
                    });
                }
            } else if (workflow.name === 'MetaAnnotation' && workflow.paramsOn) {
                result[workflow.name] = {};
                //find <prefix>_structural_annotation_stats.json
                if (fs.existsSync(outdir)) {
                    const files = fs.readdirSync(outdir);
                    files.forEach(function (file) {
                        if (file.endsWith("_structural_annotation_stats.json")) {
                            result[workflow.name]['stats'] = JSON.parse(fs.readFileSync(outdir + "/" + file));
                        }
                        if (file.endsWith("protein_size_histogram.html")) {
                            result[workflow.name]['proteinSizeHistogram'] = workflowlist[workflow.name].outdir + "/" + file;
                        }
                        if (file === "opaver_web_path.json") {
                            console.log('opaver')
                            const webPath = JSON.parse(fs.readFileSync(outdir + "/" + file));
                            console.log(webPath)
                            result[workflow.name]['opaverWebPath'] = webPath['opaver_web_path'];
                        }
                    });
                }

            } else if (workflow.name === 'MetaMAGs' && workflow.paramsOn) {
                if (fs.existsSync(outdir)) {
                    const files = fs.readdirSync(outdir);
                    result[workflow.name] = {};
                    files.forEach(function (file) {
                        if (file.endsWith("_mags_stats.json")) {
                            let stats = JSON.parse(fs.readFileSync(outdir + "/" + file));
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
                        if (file.endsWith("_barplot.png")) {
                            result[workflow.name]['barplot'] = workflowlist[workflow.name].outdir + "/" + file;
                        }
                        if (file.endsWith("_heatmap.png")) {
                            result[workflow.name]['heatmap'] = workflowlist[workflow.name].outdir + "/" + file;
                        }
                        if (file.endsWith("_kronaplot.html")) {
                            result[workflow.name]['kronaplot'] = workflowlist[workflow.name].outdir + "/" + file;
                        }
                    });
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
        // get run stats for individual workflow
        if (conf.workflow) {
            let workflowStats = {};
            workflowStats['Workflow'] = workflowlist[conf.workflow.name].full_name;
            workflowStats['Run'] = 'On';
            workflowStats['Status'] = jobStats['status'];
            workflowStats['Running Time'] = '';
            workflowStats['Start'] = '';
            workflowStats['End'] = '';
            let myStart = '';
            let myEnd = '';
            let start = jobStats['start'];
            let end = jobStats['end'];
            if (start) {
                workflowStats['Start'] = moment(start).format('YYYY-MM-DD HH:mm:ss');
                myStart = start;
            }
            if (end) {
                workflowStats['End'] = moment(end).format('YYYY-MM-DD HH:mm:ss');
                myEnd = end;
            }
            if (myStart && myEnd) {
                var ms = moment(myEnd, 'YYYY-MM-DD HH:mm:ss').diff(moment(myStart, 'YYYY-MM-DD HH:mm:ss'));
                var d = moment.duration(ms);
                workflowStats['Running Time'] = timeFormat(d);
            }
            stats.push(workflowStats);
        }
        // get run stats for metaG pipeline
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
    if (!file) {
        return { size: 0 };
    }
    if (file.toLowerCase().startsWith('http')) {
        return await ufs(file)
            .then(size => { return { size: size } })
            .catch(err => { return { size: 0 } });
    } else {
        return fs.statSync(file);
    }
}

module.exports = { submitWorkflow, generateWorkflowResult, generatePipelineResult, generateRunStats, findInputsize };
