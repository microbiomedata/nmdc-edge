/**
 * Configure the app based upon environment variables.
 *
 * This module acts as an interface between the process environment variables (i.e. `process.env.*`)
 * and the modules that consume their values. This (a) facilitates the population of variables whose
 * values depend upon file paths or other variables; (b) facilitates validation of their values and
 * the assignment of default/fallback values; and (c) reduces the number of occurrences of `process.env.*`
 * variables throughout the codebase, which can be sources of errors as some IDEs do not validate their
 * existence during development, since, at that time, they do not exist as JavaScript symbols.
 *
 * References:
 * - https://nodejs.org/en/learn/command-line/how-to-read-environment-variables-from-nodejs
 * - https://developer.mozilla.org/en-US/docs/Glossary/Falsy
 */

const path = require("path");

/**
 * Returns `true` if the value matches "true" (ignoring letter casing); otherwise, returns `false`.
 *
 * Reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/test
 *
 * Examples:
 * - f("TrUe")    => true
 * - f("fAlSe")   => false
 * - f(undefined) => false
 *
 * @param val {string|undefined} The value you want to resolve to a Boolean value
 * @return {boolean} The Boolean value
 */
const makeBoolean = (val) => {
    return typeof val === "string" ? (/^true$/i).test(val) : false;
};

/**
 * Returns the value resolved to an integer; or `undefined` if the original value is `undefined`.
 *
 * References: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/parseInt
 *
 * Examples:
 * f("123")     => 123
 * f("xyz")     => NaN (which is a Falsy value)
 * f(undefined) => undefined
 *
 * @param val {string|undefined} The value you want to resolve to an integer
 * @return {number|undefined} The integer, or `undefined`
 */
const makeIntIfDefined = (val) => {
    return typeof val === "string" ? parseInt(val, 10) : undefined;
};

// Determine several reusable directory paths based upon environment variables
// and/or the path to the directory containing this `config.js` file.
const CLIENT_BASE_DIR = path.join(__dirname, "../client");
const DATA_BASE_DIR = path.join(__dirname, "../../data")
const IO_BASE_DIR = process.env.IO_BASE_DIR || path.join(__dirname, "../../io");

const config = {
    // Name of environment in which application is running (either "production" or "development").
    // Reference: https://expressjs.com/en/advanced/best-practice-performance.html#set-node_env-to-production
    NODE_ENV: process.env.NODE_ENV || "production",
    APP: {
        // Base URL at which visitors can access the web server (e.g. "https://nmdc-edge.org").
        // Note: Some emails the server sends to visitors will contain URLs based upon this one.
        EXTERNAL_BASE_URL: process.env.APP_EXTERNAL_BASE_URL || "https://nmdc-edge.org",
        // Port number on which the web server will listen for HTTP requests.
        SERVER_PORT: makeIntIfDefined(process.env.APP_SERVER_PORT) || 5000,
        // Path to the "docs" directory on the filesystem.
        DOCS_BASE_DIR: process.env.DOCS_BASE_DIR || path.join(DATA_BASE_DIR, "docs"),
        // Version identifier of the application.
        VERSION: process.env.NMDC_EDGE_WEB_APP_VERSION || "v0.0.0-default",
    },
    AUTH: {
        // A secret string with which the web server will sign JWTs (JSON Web Tokens).
        // Note: You can generate one via: $ node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))'
        JWT_SECRET: process.env.JWT_SECRET,
        // A secret string with which the web server will "salt" submitted passwords.
        // Note: You can generate one via: $ node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))'
        OAUTH_SECRET: process.env.OAUTH_SECRET,
    },
    CLIENT: {
        // Path to the client's "build" directory on the filesystem.
        BUILD_DIR: process.env.CLIENT_BASE_DIR || path.join(CLIENT_BASE_DIR, "build"),
    },
    CROMWELL: {
        // Base URL at which HTTP clients can access the Cromwell API.
        API_BASE_URL: process.env.CROMWELL_API_BASE_URL || "http://localhost:8000",
        // Max allowed number of jobs in cromwell.
        NUM_JOBS_MAX: makeIntIfDefined(process.env.CROMWELL_NUM_JOBS_MAX) || 100000,
        // Max allowed number of jobs per user in cromwell.
        NUM_JOBS_MAX_USER: makeIntIfDefined(process.env.CROMWELL_NUM_JOBS_MAX_USER) || 10,
        // Total size of the input files allowed per job.
        // Note: 161061273600 Bytes is 150 Gibibytes (161 Gigabytes).
        JOBS_INPUT_MAX_SIZE_BYTES: makeIntIfDefined(process.env.CROMWELL_JOBS_INPUT_MAX_SIZE_BYTES) || 161061273600,
        // The type of workflow language and must be "WDL" currently.
        WORKFLOW_TYPE: process.env.CROMWELL_WORKFLOW_TYPE || "WDL",
        // The version of the workflow language. Valid versions: 'draft-2', '1.0'.
        WORKFLOW_TYPE_VERSION: process.env.CROMWELL_WORKFLOW_TYPE_VERSION || "draft-2",
    },
    CRON: {
        // Port number on which the cron web server will listen for HTTP requests.
        SERVER_PORT: makeIntIfDefined(process.env.CRON_SERVER_PORT) || 5555,
        // Cron job schedules:
        // Reference: https://crontab.guru/ (cron schedule decoder)
        SCHEDULES: {
            PIPELINE_MONITOR: process.env.CRON_PIPELINE_MONITOR_SCHEDULE || "0-59/3 * * * *",
            WORKFLOW_MONITOR: process.env.CRON_WORKFLOW_MONITOR_SCHEDULE || "1-59/3 * * * *",
            CROMWELL_MONITOR: process.env.CRON_CROMWELL_MONITOR_SCHEDULE || "2-59/3 * * * *",
            FILE_UPLOAD_MONITOR: process.env.CRON_FILE_UPLOAD_MONITOR_SCHEDULE || "0 0 * * *",
            PROJECT_STATUS_MONITOR: process.env.CRON_PROJECT_STATUS_MONITOR_SCHEDULE || "*/1 * * * *",
            PROJECT_DELETION_MONITOR: process.env.CRON_PROJECT_DELETION_MONITOR_SCHEDULE || "0 22 * * *",
            DATABASE_BACKUP_CREATOR: process.env.CRON_DATABASE_BACKUP_CREATOR_SCHEDULE || "0 1 * * *",
            DATABASE_BACKUP_PRUNER: process.env.CRON_DATABASE_BACKUP_PRUNER_SCHEDULE || "0 2 * * *",
        },
    },
    DATABASE: {
        // Host at which web server can access MongoDB server.
        SERVER_HOST: process.env.DATABASE_HOST || "localhost",
        // Port at which web server can access MongoDB server (on the specified host).
        SERVER_PORT: makeIntIfDefined(process.env.DATABASE_PORT) || 27017,
        // Credentials with which the web server can authenticate with the MongoDB server.
        USERNAME: process.env.DATABASE_USERNAME,
        PASSWORD: process.env.DATABASE_PASSWORD,
        // Name of MongoDB database.
        // TODO: Update environment variable name to `DATABASE_NAME` to be more similar to other environment variables.
        //       Note: That will require coordination with the people that manage the various deployments of this app.
        NAME: process.env.DB_NAME || "nmdcedge",
        // Path to directory in which the system will store the database backups it creates.
        BACKUP_DIR: process.env.DATABASE_BACKUP_DIR || path.join(IO_BASE_DIR, "db"),
        // Duration for which database backups will be preserved after their creation (note: 604800 seconds is 1 week).
        BACKUP_LIFETIME_SECONDS: makeIntIfDefined(process.env.DATABASE_BACKUP_LIFETIME_SECONDS) || 604800,
    },
    // Parameters related to sending email.
    // Reference: https://nodemailer.com/smtp/proxies/
    EMAIL: {
        SEND_PROJECT_STATUS_EMAILS: makeBoolean(process.env.SEND_PROJECT_STATUS_EMAILS) || false,
        FROM_ADDRESS: process.env.EMAIL_FROM_ADDRESS || "no-reply@nmdc-edge.org",
        SERVICE_IDENTIFIER: process.env.EMAIL_SERVICE_IDENTIFIER,
        SERVICE_PROXY_URL: process.env.EMAIL_SERVICE_PROXY_URL,
        // A secret string that clients can use to access the `/sendmail` endpoint.
        // Note: You can generate one via: $ node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))'
        SHARED_SECRET: process.env.EMAIL_SHARED_SECRET,
        SERVICE_USERNAME: process.env.EMAIL_SERVICE_USERNAME,
        SERVICE_PASSWORD: process.env.EMAIL_SERVICE_PASSWORD,
        MAILGUN_DOMAIN: process.env.EMAIL_MAILGUN_DOMAIN,
        MAILGUN_API_KEY: process.env.EMAIL_MAILGUN_API_KEY,
        PROJECT_STATUS_EMAIL_TEMPLATE_PATH: process.env.PROJECT_STATUS_EMAIL_TEMPLATE_PATH || path.join(DATA_BASE_DIR, "project/status.tmpl"),
    },
    FILE_UPLOADS: {
        // Note: 10737418200 Bytes is 10 Gibibytes (10.7 Gigabytes).
        // Reference: https://www.xconvert.com/unit-converter/bytes-to-gigabytes
        MAX_FILE_SIZE_BYTES: makeIntIfDefined(process.env.FILE_UPLOADS_MAX_FILE_SIZE_BYTES) || 10737418200,
        // Note: 161061273600 Bytes is 150 Gibibytes (161 Gigabytes).
        MAX_STORAGE_SIZE_BYTES: makeIntIfDefined(process.env.FILE_UPLOADS_MAX_STORAGE_SIZE_BYTES) || 161061273600,
        FILE_LIFETIME_DAYS: makeIntIfDefined(process.env.FILE_UPLOADS_FILE_LIFETIME_DAYS) || 180,
        DELETION_GRACE_PERIOD_DAYS: makeIntIfDefined(process.env.FILE_UPLOADS_DELETION_GRACE_PERIOD_DAYS) || 5,
    },
    GLOBUS: {
        // TODO: This is based upon the environment variable originally named `GLOBUS_DATA_HOME`,
        //       which was referenced in the code base, but was not defined or documented in
        //       the former `server-env-prod` template.
        // The globus service is not ready.
        DATA_HOME_DIR: process.env.GLOBUS_DATA_HOME_DIR,
    },
    IO: {
        // Directory to store sra workflow results.
        SRA_BASE_DIR: process.env.SRA_BASE_DIR || path.join(IO_BASE_DIR, "sra"),
        // Directory to store public data.
        PUBLIC_BASE_DIR: process.env.PUBLIC_BASE_DIR || path.join(IO_BASE_DIR, "public"),
        // Directory to store user uploaded files
        UPLOADED_FILES_DIR: process.env.UPLOADED_FILES_DIR || path.join(IO_BASE_DIR, "upload/files"),
        // Directory used by file uploading function.
        UPLOADED_FILES_TEMP_DIR: process.env.UPLOADED_FILES_TEMP_DIR || path.join(IO_BASE_DIR, "upload/tmp"),
        // Maximum rows to pass to UI data table
        MAX_DATATABLE_ROWS: process.env.MAX_DATATABLE_ROWS || 300000,
        // opaver_web_path
        OPAVER_WEB_DIR: process.env.OPAVER_WEB_DIR || path.join(__dirname, "../../io/opaver_web/data"),
    },
    // Parameters that influence the behavior of `Winston.js`, a logging library.
    // Reference: https://github.com/winstonjs/winston-daily-rotate-file#options
    LOGGING: {
        LOG_DIR: process.env.LOG_DIR || path.join(IO_BASE_DIR, "log"),
        LOG_LEVEL: process.env.LOG_LEVEL || "info",
        LOG_FILE_NAME_TEMPLATE: process.env.LOG_FILE_NAME_TEMPLATE || "EDGE-workflows-%DATE%.log",
        LOG_DATE_TEMPLATE: process.env.LOG_DATE_TEMPLATE || "YYYY-MM-DD",
        LOG_FILE_MAX_SIZE: process.env.LOG_FILE_MAX_SIZE || "20m",
        LOG_FILE_MAX_QUANTITY: process.env.LOG_FILE_MAX_QUANTITY || "14d",
    },
    PROJECTS: {
        // Directory to store workflow results.
        BASE_DIR: process.env.PROJECTS_BASE_DIR || path.join(IO_BASE_DIR, "projects"),
        // Number of days for which the system will preserve a project after a user opts to delete it.
        PROJECT_DELETION_GRACE_PERIOD_DAYS: makeIntIfDefined(process.env.PROJECT_DELETION_GRACE_PERIOD_DAYS) || 7,
    },
    WORKFLOWS: {
        // Directory of the workflow WDL files.
        WDL_DIR: process.env.WORKFLOWS_WDL_DIR || path.join(DATA_BASE_DIR, "workflow/WDL"),
        // Directory of the workflow templates. The Workflow templates are used for creating cromwell inputs.
        TEMPLATE_DIR: process.env.WORKFLOWS_TEMPLATE_DIR || path.join(DATA_BASE_DIR, "workflow/templates"),
    },
    NMDC: {
        // nmdc-server url for pushing metadata to submission portal
        SERVER_URL: process.env.NMDC_SERVER_URL || "https://data-dev.microbiomedata.org",
        // metadata submission json template
        METADATA_SUBMISSION_TEMPLATE: process.env.NMDC_METADATA_SUBMISSION_TEMPLATE || path.join(DATA_BASE_DIR, "project/metadata_submission.tmpl"),
    }
};

module.exports = config;