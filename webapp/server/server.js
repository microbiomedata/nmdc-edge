const express = require("express");
require("dotenv").config();
const fs = require('fs');
const path = require('path');
const https = require('https')
const cors = require("cors");
const mongoose = require("mongoose");
const bodyParser = require("body-parser");
const passport = require("passport");
const fileUpload = require('express-fileupload');
const cron = require("node-cron");
const indexRouter = require('./routes/index');
const user = require("./routes/api/user");
const project = require("./routes/api/project");
const auth_user = require("./routes/auth-api/user");
const auth_admin = require("./routes/auth-api/admin");
const logger = require('./util/logger');
const common = require("./util/common");
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

/**
 * Ensures there is a usable directory at the specified path.
 *
 * References:
 * - https://nodejs.org/api/fs.html#fsfstatsyncfd-options
 * - https://nodejs.org/api/fs.html#fsmkdirsyncpath-options
 * - https://nodejs.org/api/fs.html#fsaccesssyncpath-mode
 * - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Numbers_and_dates#octal_numbers
 */
const ensureDirectoryIsUsable = (path) => {
  try {
    // Check whether there is a directory at that path and that this process has full access to it.
    // Note: `fs.accessSync` throws an exception if access fails.
    if (fs.statSync(path).isDirectory()) {
      fs.accessSync(path, fs.constants.R_OK | fs.constants.W_OK | fs.constants.X_OK);
      console.error("Directory is usable:", path);
    } else {
      console.error("Directory is not usable:", path);
      throw new Error(`Directory is not usable: ${path}`);
    }
  } catch (error) {
    // Create a directory there to which this process has full access.
    fs.mkdirSync(path, { recursive: true, mode: 0o700 });
    console.debug("Created directory:", path);
  }
};

/**
 * Ensures directories are usable.
 */
const ensureDirectoriesAreUsable = () => {
  [
    config.IO.PUBLIC_BASE_DIR,
    config.IO.UPLOADED_FILES_DIR,
    config.IO.UPLOADED_FILES_TEMP_DIR,
    config.PROJECTS.BASE_DIR,
  ].forEach((path) => ensureDirectoryIsUsable(path));
};

/**
 * Checks whether the application can access the Cromwell API.
 *
 * Note: If the application fails to access the Cromwell API and the `doThrowException`
 *       flag is set (by default, it is not set), this function throws an Exception.
 */
const checkWhetherAppCanAccessCromwellApi = (doThrowException = false) => {
  const statusUrl = `${config.CROMWELL.API_BASE_URL}/engine/v1/status`;
  common.getData(statusUrl).then(status => {
    console.log(`Successfully accessed Cromwell API: ${statusUrl}`);
    console.log(status);
  }).catch(error => {
    console.error(`Failed to access Cromwell API: ${statusUrl}`);
    console.error(error);
    if (doThrowException) {
      throw new Error("Failed to access Cromwell API");
    }
  });
};

// Check the foundational health of the application.
ensureDirectoriesAreUsable();
checkWhetherAppCanAccessCromwellApi();

const app = express();
app.use(express.json());
app.use(fileUpload({
  //max size: 5G
  limits: { fileSize: config.FILE_UPLOADS.MAX_FILE_SIZE_BYTES },
  abortOnLimit: true,
  debug: false,
  useTempFiles: true,
  tempFileDir: config.IO.UPLOADED_FILES_TEMP_DIR
}));

// allow cross-origin requests
app.use(cors());

//Serving static files in Express
app.use('/projects', express.static(config.PROJECTS.BASE_DIR, { dotfiles: 'allow' }));
app.use('/bulksubmissions', express.static(config.PROJECTS.BULK_DIR, { dotfiles: 'allow' }));
app.use('/uploads', express.static(config.IO.UPLOADED_FILES_DIR));
app.use('/publicdata', express.static(config.IO.PUBLIC_BASE_DIR, { dotfiles: 'allow' }));
app.use('/docs', express.static(config.APP.DOCS_BASE_DIR, { dotfiles: 'allow' }));

// Bodyparser middleware
app.use(
  bodyParser.urlencoded({
    extended: false
  })
);

app.use(bodyParser.json());

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

// Passport middleware
app.use(passport.initialize());
// Passport config
require("./util/passport")(passport);

// Routes
app.get("/api/version", (req, res) => {
  // Return the version identifier of the NMDC EDGE web application.
  res.json({ version: config.APP.VERSION });
});
app.get("/api/health", async (req, res) => {
  // Check whether the app can access the Cromwell API.
  // Reference: https://cromwell.readthedocs.io/en/stable/api/RESTAPI/#return-the-current-health-status-of-any-monitored-subsystems
  const statusUrl = `${config.CROMWELL.API_BASE_URL}/engine/v1/status`;
  let appCanAccessCromwellApi = false;
  try {
    await common.getData(statusUrl);
    appCanAccessCromwellApi = true;
    console.info(`Successfully accessed Cromwell API at ${statusUrl}.`);
  } catch (error) {
    console.error(`Failed to access Cromwell API at ${statusUrl}.\n`, error);
  }

  // Check whether the app can access the Mongo server.
  // Reference: https://mongoosejs.com/docs/api/connection.html#Connection.prototype.readyState
  let appCanAccessMongoServer = false;
  try {
    appCanAccessMongoServer = mongoose.connection.readyState === 1;
    console.info(`Successfully accessed Mongo server.`);
  } catch (error) {
    console.error(`Failed to access Mongo server.\n`, error);
  }

  return res.json({
    api: true,
    cromwell: appCanAccessCromwellApi,
    mongo: appCanAccessMongoServer,
  });
});
app.use("/api/user", user);
app.use("/api/project", project);
app.use("/auth-api/user", passport.authenticate('user', { session: false }), auth_user);
app.use("/auth-api/admin", passport.authenticate('admin', { session: false }), auth_admin);
//Serving React as static files in Express and redirect url path to React client app
if (config.NODE_ENV === 'production') {
  app.use(express.static(config.CLIENT.BUILD_DIR));
  app.get('*', (req, res) => {
    res.sendFile(path.join(config.CLIENT.BUILD_DIR, 'index.html'))
  });
} else {
  app.use('/', indexRouter);

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
    //cromwellMonitor();
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
}

const port = config.APP.SERVER_PORT;
app.listen(port, () => logger.info(`HTTP ${config.NODE_ENV} server up and running on port ${port} !`));

