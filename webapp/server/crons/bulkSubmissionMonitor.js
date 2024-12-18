const fs = require('fs');
const path = require('path');
const xlsx = require('node-xlsx').default;
const ejs = require('ejs');
const randomize = require('randomatic');
const BulkSubmission = require("../models/BulkSubmission");
const Upload = require("../models/Upload");
const common = require("../util/common");
const logger = require('../util/logger');
const config = require("../config");
const { workflowlist, pipelinelist } = require("../config/workflow");

const isValidProjectName = (name) => {
  const regexp = new RegExp(/^[a-zA-Z0-9\-_.]{3,30}$/)
  return regexp.test(name.trim())
}
const isValidSRAInput = (name) => {
  const regex = /[\._]/; // Split on dot and _
  const accession = name.split(regex)[0];
  return common.fileExistsSync(`${config.IO.SRA_BASE_DIR}/${accession}/${name}`);
}

const bulkSubmissionMonitor = async () => {
  try {
    logger.debug("bulkSubmission monitor");
    //only process one request at each time
    const bulkSubmissions = await BulkSubmission.find({ 'status': 'in queue' }).sort({ updated: 1 });
    let bulkSubmission = bulkSubmissions[0];
    if (!bulkSubmission) {
      logger.debug("No bulkSubmission request to process");
      return;
    }
    //parse conf.json
    const bulkSubmission_home = path.join(config.PROJECTS.BULK_DIR, bulkSubmission.code);
    const conf_file = bulkSubmission_home + "/conf.json";
    let rawdata = fs.readFileSync(conf_file);
    let conf = JSON.parse(rawdata);
    const log = path.join(config.PROJECTS.BULK_DIR, bulkSubmission.code, "log.txt");

    logger.info("Processing bulkSubmission request: " + bulkSubmission.code);
    //set bulkSubmissionect status to 'processing'
    bulkSubmission.status = "processing";
    bulkSubmission.updated = Date.now();
    await bulkSubmission.save();
    common.write2log(log, "Validate input bulk excel file");
    logger.info("Validate input bulk excel file");
    //process request
    const bulkExcel = bulkSubmission_home + "/" + conf.bulkfile.name;
    // Parse a file
    const workSheetsFromFile = xlsx.parse(bulkExcel);
    let rows = workSheetsFromFile[0].data;
    // Remove header
    rows.shift();
    // validate inputs
    let validInput = true;
    let errMsg = '';
    let currRow = 1;
    let submissions = [];
    for (cols of rows) {
      let submission = {};
      currRow++;
      // validate project name
      if (!isValidProjectName(cols[0])) {
        validInput = false;
        errMsg += `ERROR: Row ${currRow}: Invalid project name\n`;
      } else {
        submission['proj_name'] = cols[0];
        submission['proj_desc'] = cols[1];
      }

      if (cols[2] && cols[2].trim()) {
        // validate interleaved fastq and ignore the pair-1/paire-2
        submission['interleaved'] = true;
        let fastqs = [];
        let fastqs_display = [];
        const fqs = cols[2].trim().split(/,/);
        for (fq of fqs) {
          fq = fq.trim();
          if (fq.toUpperCase().startsWith('HTTP')) {
            fastqs.push(fq);
            fastqs_display.push(fq);
          } else {
            // it's uploaded file
            const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
            if (!file) {
              validInput = false;
              errMsg += `ERROR: Row ${currRow}: Interleaved FASTQ ${fq} not found.\n`;
            } else {
              fastqs.push(`${config.IO.UPLOADED_FILES_DIR}/${file.code}`);
              fastqs_display.push(`uploads/${file.owner}/${fq}`);
            }
          }
        }
        submission['input_fastqs'] = fastqs;
        submission['input_fastqs_display'] = fastqs_display;
      } else {
        submission['interleaved'] = false;
        let pairFq1 = [];
        let pairFq1_display = [];
        let pairFq2 = [];
        let pairFq2_display = [];
        let fq1s = null;
        let fq2s = null;
        // validate the pair-1/paire-2
        if (!(cols[3] && cols[3].trim())) {
          validInput = false;
          errMsg += `ERROR: Row ${currRow}: Pair-1 FASTQ required.\n`;
        } else {
          fq1s = cols[3].trim().split(/,/);
          for (fq of fq1s) {
            fq = fq.trim();
            if (fq.toUpperCase().startsWith('HTTP')) {
              pairFq1.push(fq);
              pairFq1_display.push(fq);
            } else {
              // it's uploaded file
              const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
              if (!file) {
                validInput = false;
                errMsg += `ERROR: Row ${currRow}: Pair-1 FASTQ ${fq} not found.\n`;
              } else {
                pairFq1.push(`${config.IO.UPLOADED_FILES_DIR}/${file.code}`);
                pairFq1_display.push(`uploads/${file.owner}/${fq}`);

              }
            }
          };
        }

        if (!(cols[4] && cols[4].trim())) {
          validInput = false;
          errMsg += `ERROR: Row ${currRow}: Pair-2 FASTQ required.\n`;
        } else {
          fq2s = cols[4].trim().split(/,/);
          for (fq of fq2s) {
            fq = fq.trim();
            if (fq.toUpperCase().startsWith('HTTP')) {
              pairFq2.push(fq);
              pairFq1_display.push(fq);
            } else {
              // it's uploaded file
              const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
              if (!file) {
                validInput = false;
                errMsg += `ERROR: Row ${currRow}: Pair-2 FASTQ ${fq} not found.\n`;
              } else {
                pairFq2.push(`${config.IO.UPLOADED_FILES_DIR}/${file.code}`);
                pairFq2_display.push(`uploads/${file.owner}/${fq}`);
              }
            }
          };
        }

        if (fq1s && fq2s && fq1s.length !== fq2s.length) {
          validInput = false;
          errMsg += `ERROR: Row ${currRow}: Paire-1 FASTQ and Pair-2 FASTQ have different input fastq file counts.\n`;
        }
        if (validInput) {
          submission['input_fastqs'] = [];
          submission['input_fastqs_display'] = [];
          for (var i = 0; i < pairFq1.length; i++) {
            submission['input_fastqs'].push({ 'fq1': pairFq1[i], 'fq2': pairFq2[i] });
            submission['input_fastqs_display'].push({ 'fq1': pairFq1_display[i], 'fq2': pairFq2_display[i] });
          }
        }
      }
      submissions.push(submission);
    }

    if (validInput) {
      // submit projects
      const workflowSettings = { ...workflowlist, ...pipelinelist };
      let projects = [];

      for (submission of submissions) {
        console.log(submission)
        let code = randomize('Aa0', 16);
        let proj_home = path.join(config.PROJECTS.BASE_DIR, code);
        while (fs.existsSync(proj_home)) {
          code = randomize('Aa0', 16);
          proj_home = path.join(config.PROJECTS.BASE_DIR, code);
        }
        projects.push(code);
        // create project home
        fs.mkdirSync(proj_home);
        // create conf.json
        const template = String(fs.readFileSync(`${config.PROJECTS.CONF_TEMPLATE_DIR}/${workflowSettings[bulkSubmission.type]['project_conf_tmpl']}`));
        // render project conf template and write to conf.json
        const inputs = ejs.render(template, submission);
        await fs.promises.writeFile(`${proj_home}/conf.json`, inputs);

        // save projec to db
        const newProject = new Project({
          name: submission.proj_name,
          desc: submission.proj_desc,
          type: conf.pipeline,
          owner: bulkSubmission.owner,
          code: code
        });
        await newProject.save();
      }
      // update bulksubmission
      bulkSubmission.status = "complete";
      bulkSubmission.projects = projects;
      bulkSubmission.updated = Date.now();
      await bulkSubmission.save();
    } else {
      logger.error("Validation failed.");
      logger.error(errMsg);
      common.write2log(log, "Validation failed.");
      common.write2log(log, errMsg);
      //set bulkSubmissionect status to 'failed'
      bulkSubmission.status = "failed";
      bulkSubmission.updated = Date.now();
      await bulkSubmission.save();
    }
  } catch (err) {
    logger.error(err);
  }
};

module.exports = bulkSubmissionMonitor