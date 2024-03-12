const fs = require('fs');
const path = require("path");
const moment = require('moment');
const Upload = require("../models/Upload");
const logger = require('../util/logger');
const config = require("../config");

module.exports = function fileUploadMonitor() {
    logger.debug("file upload monitor");

    //delete file after deleteGracePeriod 
    const deleteGracePeriod = moment().subtract(config.FILE_UPLOADS.DELETION_GRACE_PERIOD_DAYS, 'days');
    Upload.find({ 'status': 'delete', 'updated': { '$lte': deleteGracePeriod } }).then(uploads => {
        var i;
        for (i = 0; i < uploads.length; i++) {
            const code = uploads[i].code;
            //delete file
            const filePath = path.join(config.IO.UPLOADED_FILES_DIR, code);
            fs.unlink(filePath, (err) => {
                if (err) {
                    logger.error("Failed to delete " + filePath + ":" + err);
                    return;
                }

                logger.info("deleted " + filePath);
            });
            //delete from database
            Upload.deleteOne({ code: code }, function (err) {
                if (err) {
                    logger.info("Failed to delete upload " + code + ":" + err);
                }
            });
        }
    });

    //change status to 'delete' if upload is older than daysKept
    const daysKept = moment().subtract(config.FILE_UPLOADS.FILE_LIFETIME_DAYS, 'days');
    Upload.find({ status: 'live', 'created': { '$lte': daysKept } }).then(uploads => {
        var i;
        for (i = 0; i < uploads.length; i++) {
            const code = uploads[i].code;
            logger.info("mark file for deleting " + code);
            Upload.findOne({ code: code }).then(upload => {
                if (!upload) {
                    logger.error("Upload not found " + code);
                } else {
                    upload.status = 'delete';
                    upload.updated = Date.now();
                    upload.save().then().catch(err => {
                        logger.error("Failed to update upload " + code + ":" + err);
                    });
                }
            });
        }
    });
}