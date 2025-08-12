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
  if(!name || name.trim() === '') {
    return false;
  }
  const regexp = new RegExp(/^[a-zA-Z0-9\-_.]{3,30}$/)
  return regexp.test(name.trim())
}
const isValidSRAInput = (name, accession) => {
  return fs.existsSync(`${config.IO.SRA_BASE_DIR}/${accession}/${name}`);
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
    let rows = workSheetsFromFile[0].data.filter(row => {
        // Check if all cells in the row are empty (null, undefined, or empty string after trim)
        return row.some(cell => cell !== null && cell !== undefined && String(cell).trim() !== '');
    });
    // Remove header
    rows.shift();
    // validate inputs
    let validInput = true;
    let errMsg = '';
    let currRow = 1;
    let submissions = [];

    for (cols of rows) {
      let submission = {};
      let dataSource = cols[2] ? cols[2].trim() : 'Uploaded File';
      currRow++;
      if(cols.length < 4) {
        validInput = false;
        errMsg += `ERROR: Row ${currRow}: Invalid input.\n`;
        continue;
      } 
      // validate project name
      if (!isValidProjectName(cols[0])) {
        validInput = false;
        errMsg += `ERROR: Row ${currRow}: Invalid project name\n`;
      } else {
        submission['proj_name'] = cols[0];
        submission['proj_desc'] = cols[1];
      }
      //get Sequencing Platform, default is Illumina
      if (cols[6] && cols[6] === 'PacBio') {
        submission['platform'] = 'PacBio';
        submission['shortRead'] = false;
      } else {
        submission['platform'] = 'Illumina';
        submission['shortRead'] = true;
      }

      if (cols[3] && cols[3].trim()) {
        // validate Interleaved or Single-end Illumina/PacBio fastq and ignore the Illumina Pair-1/paire-2
        submission['interleaved'] = true;
        let fastqs = [];
        let fastqs_display = [];
        const fqs = cols[3].split(/,/);
        for (fq of fqs) {
          fq = fq.trim();
          if (dataSource === 'HTTP(s) URL') {
            fastqs.push(fq);
            fastqs_display.push(fq);
          } else if (dataSource === 'Retrieved SRA Data') {
            const regex = /[\._]/; // Split on dot and _
            const accession = fq.split(regex)[0];
            if(isValidSRAInput(fq, accession)) {
              fastqs.push(`${config.IO.SRA_BASE_DIR}/${accession}/${fq}`);
              fastqs_display.push(`sradata/${accession}/${fq}`);
            } else {
              validInput = false;
              errMsg += `ERROR: Row ${currRow}: ${dataSource}: Interleaved or Single-end Illumina/PacBio FASTQ: ${fq} not found.\n`;
            }
          } else {
            // it's uploaded file
            const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
            if (!file) {
              validInput = false;
              errMsg += `ERROR: Row ${currRow}: ${dataSource}: Interleaved or Single-end Illumina/PacBio FASTQ: ${fq} not found.\n`;
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
        if(submission['platform'] === 'PacBio') {
          validInput = false;
          errMsg += `ERROR: Row ${currRow}: PacBio FASTQ required.\n`;
        } else {
          let pairFq1 = [];
          let pairFq1_display = [];
          let pairFq2 = [];
          let pairFq2_display = [];
          let fq1s = null;
          let fq2s = null;
          // validate the Illumina Pair-1/paire-2
          if (!(cols[4] && cols[4].trim())) {
            validInput = false;
            errMsg += `ERROR: Row ${currRow}: Illumina Paired-end R1 required.\n`;
          } else {
            fq1s = cols[4].split(/,/);
            for (fq of fq1s) {
              fq = fq.trim();
              if (dataSource === 'HTTP(s) URL') {
                pairFq1.push(fq);
                pairFq1_display.push(fq);
              } else if (dataSource === 'Retrieved SRA Data') {
                const regex = /[\._]/; // Split on dot and _
                const accession = fq.split(regex)[0];
                if(isValidSRAInput(fq, accession)) {
                  pairFq1.push(`${config.IO.SRA_BASE_DIR}/${accession}/${fq}`);
                  pairFq1_display.push(`sradata/${accession}/${fq}`);
                } else {
                  validInput = false;
                  errMsg += `ERROR: Row ${currRow}: ${dataSource}: Illumina Paired-end R1 FASTQ: ${fq} not found.\n`;
                }
              } else {
                // it's uploaded file
                const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
                if (!file) {
                  validInput = false;
                  errMsg += `ERROR: Row ${currRow}: ${dataSource}: Illumina Paired-end R1 FASTQ: ${fq} not found.\n`;
                } else {
                  pairFq1.push(`${config.IO.UPLOADED_FILES_DIR}/${file.code}`);
                  pairFq1_display.push(`uploads/${file.owner}/${fq}`);
                }
              } 
            };
          }

          if (!(cols[5] && cols[5].trim())) {
            validInput = false;
            errMsg += `ERROR: Row ${currRow}: Illumina Paired-end R2 required.\n`;
          } else {
            fq2s = cols[5].split(/,/);
            for (fq of fq2s) {
              fq = fq.trim();
              if (dataSource === 'HTTP(s) URL') {
                pairFq2.push(fq);
                pairFq2_display.push(fq);
              } else if (dataSource === 'Retrieved SRA Data') {
                const regex = /[\._]/; // Split on dot and _
                const accession = fq.split(regex)[0];
                if(isValidSRAInput(fq, accession)) {
                  pairFq2.push(`${config.IO.SRA_BASE_DIR}/${accession}/${fq}`);
                  pairFq2_display.push(`sradata/${accession}/${fq}`);
                } else {
                  validInput = false;
                  errMsg += `ERROR: Row ${currRow}: ${dataSource}: Illumina Paired-end R2 FASTQ: ${fq} not found.\n`;
                }
              } else {
                // it's uploaded file
                const file = await Upload.findOne({ name: { $eq: fq }, status: { $ne: 'delete' } });
                if (!file) {
                  validInput = false;
                  errMsg += `ERROR: Row ${currRow}: ${dataSource}: Illumina Paired-end R2 FASTQ: ${fq} not found.\n`;
                } else {
                  pairFq2.push(`${config.IO.UPLOADED_FILES_DIR}/${file.code}`);
                  pairFq2_display.push(`uploads/${file.owner}/${fq}`);
                }
              } 
            };
          }

          if (fq1s && fq2s && fq1s.length !== fq2s.length) {
            validInput = false;
            errMsg += `ERROR: Row ${currRow}: Illumina Paired-end R1 and Illumina Paired-end R2 have different input fastq file counts.\n`;
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
      }
      submissions.push(submission);
    }

    if (validInput) {
      // submit projects
      const workflowSettings = { ...workflowlist, ...pipelinelist };
      let projects = [];
      let submission = null;
      for (submission of submissions) {
        //console.log(submission)
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