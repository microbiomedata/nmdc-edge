const express = require("express");
require("dotenv").config();
const cors = require("cors");
const mongoose = require("mongoose");
const cron = require("node-cron");
const logger = require('./util/logger');
const pipelineMonitor = require("./crons/pipelineMonitor");
const workflowMonitor = require("./crons/workflowMonitor");
const workflowBigMemMonitor = require("./crons/workflowBigMemMonitor");
const bulkSubmissionMonitor = require("./crons/bulkSubmissionMonitor");
const cromwellMonitor = require("./crons/cromwellMonitor");
const fileUploadMonitor = require("./crons/fileUploadMonitor");
const projectMonitor = require("./crons/projectMonitor");
const projectStatusMonitor = require("./crons/projectStatusMonitor");
const dbBackup = require("./crons/dbBackup");
const dbBackupClean = require("./crons/dbBackupClean");
const config = require("./config");

const app = express();
app.use(express.json());

// allow cross-origin requests
app.use(cors());

// DB Config
const db = `mongodb://${config.DATABASE.SERVER_HOST}:${config.DATABASE.SERVER_PORT}/${config.DATABASE.NAME}`;
// Connect to MongoDB 
mongoose
  .connect(
    db,
    {
      authSource: "admin",
      user: config.DATABASE.USERNAME,
      pass: config.DATABASE.PASSWORD,
      useCreateIndex: true,
      useNewUrlParser: true,
      useUnifiedTopology: true,
    }
  )
  .then(() => logger.info("MongoDB successfully connected"))
  .catch(err => logger.error("Failed to connect to MongoDB server:", err));

//cron jobs
// monitor pipeline requests on every 1 minute
cron.schedule(config.CRON.SCHEDULES.PIPELINE_MONITOR, function () {
  pipelineMonitor();
});
// monitor workflow requests on every 3 minutes 
cron.schedule(config.CRON.SCHEDULES.WORKFLOW_MONITOR, function () {
  workflowMonitor();
});
// monitor workflow requests on every 3 minutes 
cron.schedule(config.CRON.SCHEDULES.WORKFLOW_BIG_MEM_MONITOR, function () {
  workflowBigMemMonitor();
});
// monitor bulk submission requests on every 3 minutes 
cron.schedule(config.CRON.SCHEDULES.BULKSUBMISSION_MONITOR, function () {
  bulkSubmissionMonitor();
});
// monitor cromwell jobs on every 3 minutes 
cron.schedule(config.CRON.SCHEDULES.CROMWELL_MONITOR, function () {
  cromwellMonitor();
});

//monitor uploads every day at midnight
cron.schedule(config.CRON.SCHEDULES.FILE_UPLOAD_MONITOR, function () {
  fileUploadMonitor();
});

// monitor project status on every 1 minute
cron.schedule(config.CRON.SCHEDULES.PROJECT_STATUS_MONITOR, function () {
  projectStatusMonitor();
});
//monitor project deletion every day at 10pm
cron.schedule(config.CRON.SCHEDULES.PROJECT_DELETION_MONITOR, function () {
  projectMonitor();
});
//backup nmdcedge DB every day at 10pm
cron.schedule(config.CRON.SCHEDULES.DATABASE_BACKUP_CREATOR, function () {
  dbBackup();
});
//delete older DB backups every day at 12am
cron.schedule(config.CRON.SCHEDULES.DATABASE_BACKUP_PRUNER, function () {
  dbBackupClean();
});

const port = config.CRON.SERVER_PORT;
app.listen(port, () => logger.info(`HTTP CRON server up and running on port ${port} !`));

