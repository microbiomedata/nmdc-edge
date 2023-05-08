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

const app = express();
app.use(express.json());
app.use(fileUpload({
  //max size: 5G
  limits: { fileSize: process.env.FILEUPLOAD_MAX_SIZE_BYTES },
  abortOnLimit: true,
  debug: false,
  useTempFiles: true,
  tempFileDir: process.env.FILEUPLOAD_TMP_DIR
}));

// allow cross-origin requests
app.use(cors());

//Serving static files in Express
app.use('/projects', express.static(process.env.PROJECT_HOME, { dotfiles: 'allow' }));
app.use('/uploads', express.static(process.env.FILEUPLOAD_FILE_DIR));
app.use('/publicdata', express.static(process.env.PUBLIC_DATA_HOME));
app.use('/docs', express.static(process.env.DOCS_HOME, { dotfiles: 'allow' }));

// Bodyparser middleware
app.use(
  bodyParser.urlencoded({
    extended: false
  })
);

app.use(bodyParser.json());

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
if (process.env.NODE_ENV === 'prod') {
  app.use(express.static(process.env.UI_BUILD_PATH));
  app.get('*', (req, res) => {
    res.sendFile(path.join(process.env.UI_BUILD_PATH, 'index.html'))
  });
} else {
  app.use('/', indexRouter);

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
    //cromwellMonitor();
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
}

const port = process.env.PORT;
if (process.env.HTTPS_KEY && process.env.HTTPS_CERT) {
  https.createServer({
    key: fs.readFileSync(process.env.HTTPS_KEY),
    cert: fs.readFileSync(process.env.HTTPS_CERT)
  }, app).listen(port, function () {
    logger.info(`HTTPS ${process.env.NODE_ENV} server up and running on port ${port} !`);
  })
}
else {
  app.listen(port, () => logger.info(`HTTP ${process.env.NODE_ENV} server up and running on port ${port} !`));
}

