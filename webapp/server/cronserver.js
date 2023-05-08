const express = require("express");
require("dotenv").config();
const cors = require("cors");
const mongoose = require("mongoose");
const cron = require("node-cron");
const logger = require('./util/logger');
const pipelineMonitor = require("./crons/pipelineMonitor");
const workflowMonitor = require("./crons/workflowMonitor");
const workflowBigMemMonitor = require("./crons/workflowBigMemMonitor");
const cromwellMonitor = require("./crons/cromwellMonitor");
const fileUploadMonitor = require("./crons/fileUploadMonitor");
const projectMonitor = require("./crons/projectMonitor");
const projectStatusMonitor = require("./crons/projectStatusMonitor");

const app = express();
app.use(express.json());

// allow cross-origin requests
app.use(cors());

// DB Config
const db = process.env.MONGO_URI;
// Connect to MongoDB 
mongoose
  .connect(
    db,
    { useCreateIndex: true, useNewUrlParser: true, useUnifiedTopology: true }
  )
  .then(() => logger.info("MongoDB successfully connected"))
  .catch(err => logger.error(err));

//cron jobs
// monitor pipeline requests on every 1 minute
cron.schedule(process.env.CRON_PIPELINE_MONITOR, function () {
  pipelineMonitor();
});
// monitor workflow requests on every 3 minutes 
cron.schedule(process.env.CRON_WORKFLOW_MONITOR, function () {
  workflowMonitor();
});
// monitor workflow requests on every 3 minutes 
cron.schedule(process.env.CRON_WORKFLOW_BIG_MEM_MONITOR, function () {
  workflowBigMemMonitor();
});
// monitor cromwell jobs on every 3 minutes 
cron.schedule(process.env.CRON_CROMWELL_MONITOR, function () {
  cromwellMonitor();
});

//monitor uploads every day at midnight
cron.schedule(process.env.CRON_FILEUPLOAD_MONITOR, function () {
  fileUploadMonitor();
});

// monitor project status on every 1 minute
cron.schedule(process.env.CRON_PROJECT_STATUS_MONITOR, function () {
  projectStatusMonitor();
});
//monitor project deletion every day at 10pm
cron.schedule(process.env.CRON_PROJECT_MONITOR, function () {
  projectMonitor();
});

const port = process.env.CRON_PORT;
app.listen(port, () => logger.info(`HTTP CRON server up and running on port ${port} !`));

