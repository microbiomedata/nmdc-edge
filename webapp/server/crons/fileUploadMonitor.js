const fs = require('fs');
const moment = require('moment');
const Upload = require("../models/Upload");
const logger = require('../util/logger');

module.exports = function fileUploadMonitor() {
    logger.debug("file upload monitor");

    //delete file after deleteGracePeriod 
    const deleteGracePeriod = moment().subtract(process.env.FILEUPLOAD_DELETE_GRACE_PERIOD, 'days');
    Upload.find({ 'status': 'delete', 'updated': { '$lte': deleteGracePeriod } }).then(uploads => {
        var i;
        for (i = 0; i < uploads.length; i++) {
            const code = uploads[i].code;
            //delete file
            const path = process.env.FILEUPLOAD_FILE_DIR + "/" + code;
            fs.unlink(path, (err) => {
                if (err) {
                    logger.error("Failed to delete " + path + ":" + err);
                    return;
                }

                logger.info("deleted " + path);
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
    const daysKept = moment().subtract(process.env.FILEUPLOAD_DAYS_KEPT, 'days');
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