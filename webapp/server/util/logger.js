const winston = require("winston");
const DailyRotateFile = require("winston-daily-rotate-file");

const logFormat = winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp({format: 'YYYY-MM-DD HH:mm:ss'}),
    winston.format.align(),
    winston.format.printf(
        info => `${info.timestamp} ${info.level}: ${info.message}`,
    ));

const transport = new DailyRotateFile({
    filename: process.env.LOG_FILE,
    datePattern: process.env.LOG_DATE_PATTERN,
    zippedArchive: false,
    maxSize: process.env.LOG_MAX_SIZE,
    maxFiles: process.env.LOG_MAX_FILES,
    prepend: true,
    level: process.env.LOG_LEVEL,
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