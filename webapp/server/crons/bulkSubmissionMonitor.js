const fs = require('fs');
const path = require('path');
const xlsx = require('node-xlsx').default;
const BulkSubmission = require("../models/BulkSubmission");
const common = require("../util/common");
const logger = require('../util/logger');
const config = require("../config");

module.exports = async function bulkSubmissionMonitor() {
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

  logger.info("Processing bulkSubmission request: " + bulkSubmission.code)
  //set bulkSubmissionect status to 'processing'
  bulkSubmission.status = "processing";
  bulkSubmission.updated = Date.now();
  //await bulkSubmission.save();
  common.write2log(path.join(config.PROJECTS.BULK_DIR, bulkSubmission.code, "log.txt"), "Validate input bulk excel file");
  logger.info("Validate input bulk excel file");
  //process request
  const bulkExcel = bulkSubmission_home + "/" + conf.bulkfile.name;
  // Parse a file
  const workSheetsFromFile = xlsx.parse(bulkExcel);
  console.log(workSheetsFromFile[0].data)
};
