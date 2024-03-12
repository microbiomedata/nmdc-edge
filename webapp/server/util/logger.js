const winston = require("winston");
const DailyRotateFile = require("winston-daily-rotate-file");
const path = require("path");
const config = require("../config");

const logFormat = winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp({format: 'YYYY-MM-DD HH:mm:ss'}),
    winston.format.align(),
    winston.format.printf(
        info => `${info.timestamp} ${info.level}: ${info.message}`,
    ));

const transport = new DailyRotateFile({
    filename: path.join(config.LOGGING.LOG_DIR, config.LOGGING.LOG_FILE_NAME_TEMPLATE),
    datePattern: config.LOGGING.LOG_DATE_TEMPLATE,
    zippedArchive: false,
    maxSize: config.LOGGING.LOG_FILE_MAX_SIZE,
    maxFiles: config.LOGGING.LOG_FILE_MAX_QUANTITY,
    prepend: true,
    level: config.LOGGING.LOG_LEVEL,
});

transport.on('rotate', function (oldFilename, newFilename) {
    // call function like upload to s3 or on cloud
});

const logger = winston.createLogger({
    format: logFormat,
    transports: [
        transport,
        new winston.transports.Console({
            level: "debug",
        }),
    ]
});

module.exports = logger;