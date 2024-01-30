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
const pipelineMonitor = require("./crons/pipelineMonitor");
const workflowMonitor = require("./crons/workflowMonitor");
const workflowBigMemMonitor = require("./crons/workflowBigMemMonitor");
const cromwellMonitor = require("./crons/cromwellMonitor");
const fileUploadMonitor = require("./crons/fileUploadMonitor");
const projectMonitor = require("./crons/projectMonitor");
const projectStatusMonitor = require("./crons/projectStatusMonitor");
const dbBackup = require("./crons/dbBackup");
const dbBackupClean = require("./crons/dbBackupClean");
const config = require("./config");

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
app.use('/uploads', express.static(config.IO.UPLOADED_FILES_DIR));
app.use('/publicdata', express.static(config.IO.PUBLIC_BASE_DIR));
app.use('/docs', express.static(config.APP.DOCS_BASE_DIR, { dotfiles: 'allow' }));

// Bodyparser middleware
app.use(
  bodyParser.urlencoded({
    extended: false
  })
);

app.use(bodyParser.json());

// DB Config
const db = `mongodb://${config.DB.HOST}:${config.DB.PORT}/${config.DB.DATABASE_NAME}`;
// Connect to MongoDB 
mongoose
  .connect(
    db,
    { useCreateIndex: true, useNewUrlParser: true, useUnifiedTopology: true }
  )
  .then(() => logger.info("MongoDB successfully connected"))
  .catch(err => logger.error(err));

// Passport middleware
app.use(passport.initialize());
// Passport config
require("./util/passport")(passport);

// Routes
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
if (config.APP.SERVER_SSL_PRIVATE_KEY_FILE_PATH && config.APP.SERVER_SSL_CERT_CHAIN_FILE_PATH) {
  https.createServer({
    key: fs.readFileSync(config.APP.SERVER_SSL_PRIVATE_KEY_FILE_PATH),
    cert: fs.readFileSync(config.APP.SERVER_SSL_CERT_CHAIN_FILE_PATH)
  }, app).listen(port, function () {
    logger.info(`HTTPS ${config.NODE_ENV} server up and running on port ${port} !`);
  })
}
else {
  app.listen(port, () => logger.info(`HTTP ${config.NODE_ENV} server up and running on port ${port} !`));
}

