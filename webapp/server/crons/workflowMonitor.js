const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const { workflowlist } = require("../config/workflow");
const common = require("../util/common");
const logger = require('../util/logger');
const { submitWorkflow, findInputsize } = require("../util/workflow");

module.exports = function workflowMonitor() {
    logger.debug("workflow monitor");
    //only process one job at each time based on job updated time
    CromwellJob.find({ 'status': { $in: ['Submitted', 'Running'] } }).sort({ updated: 1 }).then(jobs => {
        //submit request only when the current cromwell running jobs less than the max allowed jobs
        if (jobs.length >= process.env.MAX_CROMWELL_JOBS) {
            return;
        }
        //get current running/submitted projects' input size
        let jobInputsize = 0;
        jobs.forEach(job => {
            jobInputsize += job.inputsize;
        });
        //only process one request at each time
        Project.find({ 'type': { $nin: ['virus_plasmid', 'Metagenome Pipeline'] }, 'status': 'in queue' }).sort({ updated: 1 }).then(async projs => {
            let proj = projs[0];
            if (!proj) {
                logger.debug("No workflow request to process");
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
                logger.debug("Project " + proj.code + " input size exceeded the limit.");
                //fail project
                proj.status = 'failed';
                proj.updated = Date.now();
                proj.save();
                common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "input size exceeded the limit.");
                return;
            }
            if ((jobInputsize + inputsize) > process.env.MAX_CROMWELL_JOBS_INPUTSIZE) {
                logger.debug("Cromwell is busy.");
                return;
            }

            logger.info("Processing workflow request: " + proj.code)
            //set project status to 'processing'
            proj.status = "processing";
            proj.updated = Date.now();
            proj.save().then(proj => {
                common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "Generate WDL and inputs json");
                logger.info("Generate WDL and inputs json");
                //process request
                const workflow = conf.workflow;
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
                        logger.error("Failed to generate WDL for project " + proj.code);
                        reject("Failed to generate WDL for project " + proj.code);
                    }
                });
                let promise2 = new Promise(function (resolve, reject) {
                    generateInputs(proj_home, workflow, proj).then(inputs => {
                        if (inputs) {
                            resolve(proj);
                        } else {
                            logger.error("Failed to generate inputs.json for project " + proj.code);
                            reject("Failed to generate inputs.json for project " + proj.code);
                        }
                    })
                });

                Promise.all([promise1, promise2]).then(function (projs) {
                    //submit workflow to cromwell
                    common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", "submit workflow to cromwell");
                    logger.info("submit workflow to cromwell");
                    submitWorkflow(proj, workflow, inputsize);
                }).catch(function (err) {
                    proj.status = 'failed';
                    proj.updated = Date.now();
                    proj.save();
                    common.write2log(process.env.PROJECT_HOME + "/" + proj.code + "/log.txt", err);
                    logger.error(err);
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

function generateWDL(proj_home, workflow) {
    //build wdl
    let imports = '';
    let mainWDL = '';

    const workflowSettings = workflowlist[workflow.name];
    const workflowname = workflow.name;
    const workflowalias = workflowSettings['name'];

    const wdlVersion = workflowSettings['wdl_version'];
    if(wdlVersion === '1.0') {
        imports = "version 1.0\n";
    }

    imports += 'import "' + workflowSettings['wdl'] + '" as ' + workflowname + "\n";
    if(workflowname === 'MetaAnnotation') {
        imports += 'import "annotation_output.wdl" as MetaAnnotationOutput' + "\n";
    }
    const tmpl = process.env.WORKFLOW_TEMPLATE_HOME + "/" + workflowSettings['wdl_tmpl'];
    let templWDL = String(fs.readFileSync(tmpl));
    templWDL = templWDL.replace(/<WORKFLOW>/g, workflowname);
    templWDL = templWDL.replace(/<ALIAS>/g, workflowalias);
    mainWDL += templWDL;

    let wdl = imports + "\n";
    wdl += "workflow main_workflow {\n";
    wdl += mainWDL + "\n}\n";
    //write to pipeline.wdl
    fs.writeFileSync(proj_home + '/pipeline.wdl', wdl);
    return true;
}

async function generateInputs(proj_home, workflow, proj) {
    //build pipeline_inputs.json
    let inputs = "{\n";

    const workflowSettings = workflowlist[workflow.name];
    const workflowname = workflow.name;
    const tmpl = process.env.WORKFLOW_TEMPLATE_HOME + "/" + workflowSettings['inputs_tmpl'];
    let templInputs = String(fs.readFileSync(tmpl));
    templInputs = templInputs.replace(/<WORKFLOW>/g, workflowname);

    //workflow specific inputs
    if (workflow.name === 'ReadbasedAnalysis') {
        let reads = workflow['reads'];
        templInputs = templInputs.replace(/<READS>/, JSON.stringify(reads));
        templInputs = templInputs.replace(/<ENABLED_TOOLS>/, JSON.stringify(workflow['enabled_tools']));
        templInputs = templInputs.replace(/<PAIRED>/, workflow['paired']);
        templInputs = templInputs.replace(/<PREFIX>/, '"' + proj.name + '"');
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');

    } else if (workflow.name === 'ReadsQC' || workflow.name === 'MetaAssembly' || workflow.name === 'Metatranscriptome') {
        let interleaved = workflow['input_fastq']['interleaved'];
        let input_fastq = workflow['input_fastq']['fastqs'];

        templInputs = templInputs.replace(/<PREFIX>/, '"' + proj.name + '"');
        templInputs = templInputs.replace(/<PROJNAME>/g, '"' + proj.name + '"');
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        templInputs = templInputs.replace(/<INTERLEAVED>/, interleaved);
        if (interleaved) {
            //inputs 
            let inputs_fq = [];
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

            if (workflow.name === 'Metatranscriptome') {
                templInputs = templInputs.replace(/<INPUT_FILE_SINGLE>/, '"' + inputs_fq[0] + '"');
                templInputs = templInputs.replace(/<INPUT_FQ1>/, '""');
                templInputs = templInputs.replace(/<INPUT_FQ2>/, '""');
            } else {
                templInputs = templInputs.replace(/<INPUT_FILES>/, JSON.stringify(inputs_fq));
                templInputs = templInputs.replace(/<INPUT_FILE>/, JSON.stringify(inputs_fq));
                templInputs = templInputs.replace(/<INPUT_FQ1>/, '[]');
                templInputs = templInputs.replace(/<INPUT_FQ2>/, '[]');
            }
        } else {
            //inputs 
            let inputs_fq1 = [];
            let inputs_fq2 = [];
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
                if (fq2.startsWith(process.env.FILEUPLOAD_FILE_DIR)) {
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
            if (workflow.name === 'Metatranscriptome') {
                //only allow 1 input set
                templInputs = templInputs.replace(/<INPUT_FQ1>/, '"' + inputs_fq1[0] + '"');
                templInputs = templInputs.replace(/<INPUT_FQ2>/, '"' + inputs_fq2[0] + '"');
                templInputs = templInputs.replace(/<INPUT_FILE_SINGLE>/, '""');
            } else {
                templInputs = templInputs.replace(/<INPUT_FQ1>/, JSON.stringify(inputs_fq1));
                templInputs = templInputs.replace(/<INPUT_FQ2>/, JSON.stringify(inputs_fq2));
                templInputs = templInputs.replace(/<INPUT_FILES>/, '[]');
                templInputs = templInputs.replace(/<INPUT_FILE>/, '[]');
            }
        }

    } else if (workflow.name === 'MetaAnnotation') {
        let input_fasta = workflow['input_fasta'];
        templInputs = templInputs.replace(/<INPUT_FILE>/, '"' + input_fasta + '"');
        templInputs = templInputs.replace(/<PROJID>/, '"' + proj.name + '"');
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');

    } else if (workflow.name === 'MetaMAGs') {
        let input_contig = workflow['input_contig'];
        templInputs = templInputs.replace(/<CONTIG_FILE>/, '"' + input_contig + '"');

        let input_sam = workflow['input_sam'];
        templInputs = templInputs.replace(/<SAM_FILE>/, '"' + input_sam + '"');

        let input_gff = workflow['input_gff'];
        templInputs = templInputs.replace(/<GFF_FILE>/, '"' + input_gff + '"');

        let input_map = workflow['input_map'];
        if (input_map) {
            templInputs = templInputs.replace(/<MAP_FILE>/, '"' + input_map + '"');
        } else {
            templInputs = templInputs.replace(/<MAP_FILE>/, 'null');
        }

        templInputs = templInputs.replace(/<PROJ_NAME>/, '"' + proj.name + '"');
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');

    } else if (workflow.name === 'EnviroMS') {
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        templInputs = templInputs.replace(/<FILE_PATHS>/, JSON.stringify(workflow['file_paths']));
        templInputs = templInputs.replace(/<OUT_TYPE>/, '"' + workflow['output_type'] + '"');
        templInputs = templInputs.replace(/<CALIBRATE>/, workflow['calibrate']);
        let cal_ref = workflow['calibration_ref_file_path'];
        if (cal_ref) {
            templInputs = templInputs.replace(/<CALIBRATATION_REF_PATH>/, '"' + cal_ref + '"');
        } else {
            templInputs = templInputs.replace(/<CALIBRATATION_REF_PATH>/, 'null');
        }
        templInputs = templInputs.replace(/<COREMS_JSON_PATH>/, '"' + workflow['corems_json_path'] + '"');
        templInputs = templInputs.replace(/<POLARITY>/, '"' + workflow['polarity'] + '"');
        templInputs = templInputs.replace(/<IS_CENTROID>/, workflow['is_centroid']);
        templInputs = templInputs.replace(/<START_SCAN>/, workflow['raw_file_start_scan']);
        templInputs = templInputs.replace(/<FINAL_SCAN>/, workflow['raw_file_final_scan']);
        templInputs = templInputs.replace(/<PLOT_MZ_E>/, workflow['plot_mz_error']);
        templInputs = templInputs.replace(/<PLOT_MS_A>/, workflow['plot_ms_assigned_unassigned']);
        templInputs = templInputs.replace(/<PLOT_C>/, workflow['plot_c_dbe']);
        templInputs = templInputs.replace(/<PLOT_VAN>/, workflow['plot_van_krevelen']);
        templInputs = templInputs.replace(/<PLOT_MS_C>/, workflow['plot_ms_classes']);
        templInputs = templInputs.replace(/<PLOT_MZ_E_C>/, workflow['plot_mz_error_classes']);
    } else if (workflow.name === 'virus_plasmid') {
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        templInputs = templInputs.replace(/<FASTA>/, JSON.stringify(workflow['input_fasta']));
        // templInputs = templInputs.replace(/<ENABLED_MODULES>/, JSON.stringify(workflow['enabled_modules']));
        templInputs = templInputs.replace(/<MIN_SCORE>/, JSON.stringify(workflow['min_score']));
        templInputs = templInputs.replace(/<MIN_VIRUS_HALLMARK>/, JSON.stringify(workflow['min_virus_hallmark']));
        templInputs = templInputs.replace(/<MIN_PLASMID_HALLMARK>/, JSON.stringify(workflow['min_plasmid_hallmark']));
        templInputs = templInputs.replace(/<OPTION>/, JSON.stringify(workflow['option']));
        templInputs = templInputs.replace(/<MIN_PLASMID_HALLMARK_SHORT_SEQS>/, JSON.stringify(workflow['min_plasmid_hallmarks_short_seqs']));
        templInputs = templInputs.replace(/<MIN_VIRUS_HALLMARK_SHORT_SEQS>/, JSON.stringify(workflow['min_virus_hallmarks_short_seqs']));
        templInputs = templInputs.replace(/<MIN_PLASMID_MARKER_ENRICHMENT>/, JSON.stringify(workflow['min_plasmid_marker_enrichment']));
        templInputs = templInputs.replace(/<MIN_VIRUS_MARKER_ENRICHMENT>/, JSON.stringify(workflow['min_virus_marker_enrichment']));
        templInputs = templInputs.replace(/<MAX_USCG>/, JSON.stringify(workflow['max_uscg']));
        templInputs = templInputs.replace(/<SCORE_CALIBRATION>/, JSON.stringify(workflow['score_calibration']));
        templInputs = templInputs.replace(/<FDR>/, JSON.stringify(workflow['fdr']));
    } else if (workflow.name === 'Metaproteomics') {
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + proj_home + "/" + workflowSettings['outdir'] + '"');
        templInputs = templInputs.replace(/<RAW_FILE>/, JSON.stringify(workflow['input_raw']));
        templInputs = templInputs.replace(/<FAA_FILE>/, JSON.stringify(workflow['input_fasta']));
        templInputs = templInputs.replace(/<GFF_FILE>/, JSON.stringify(workflow['input_gff']));
        templInputs = templInputs.replace(/<THERMO_RAW>/, JSON.stringify(workflow['thermo_raw']));
        templInputs = templInputs.replace(/<QVALUE_THRESHOLD>/, JSON.stringify(workflow['qvalue_threshold']));
        templInputs = templInputs.replace(/<STUDY>/, JSON.stringify(workflow['study']));
    } else if (workflow.name === 'sra2fastq') {
        const sraDataDir = process.env.SRA_DATA_HOME;
        //accessions string to arrray
        const accessions = workflow['accessions'].toUpperCase().split(/\s*(?:,|$)\s*/);
        //filter out accessions already exist in sra data home
        const accessions4workflow = accessions.filter(
            accession => !fs.existsSync(sraDataDir + "/" + accession)
        );
        templInputs = templInputs.replace(/<ACCESSIONS>/, JSON.stringify(accessions4workflow));
        templInputs = templInputs.replace(/<OUTDIR>/, '"' + sraDataDir + '"');
    }
    inputs += templInputs + "\n";
    inputs += "}\n";
    //write to pipeline_inputs.json
    fs.writeFileSync(proj_home + '/pipeline_inputs.json', inputs);
    return true;
}
