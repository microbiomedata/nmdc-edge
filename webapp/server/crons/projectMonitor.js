const fs = require('fs');
const path = require("path");
const moment = require('moment');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const logger = require('../util/logger');
const config = require("../config");

module.exports = function projectMonitor() {
    logger.debug("project monitor");

    //delete file after deleteGracePeriod 
    const deleteGracePeriod = moment().subtract(config.PROJECTS.PROJECT_DELETION_GRACE_PERIOD_DAYS, 'days');
    Project.find({ 'status': 'delete', 'updated': { '$lte': deleteGracePeriod } }).then(projs => {
        var i;
        for (i = 0; i < projs.length; i++) {
            const code = projs[i].code;
            logger.info("delete project: " + code)
            const dirPath = path.join(config.PROJECTS.BASE_DIR, code);
            // delete directory recursively
            try {
                fs.rmdirSync(dirPath, { recursive: true });
                logger.info("deleted " + dirPath);
            } catch (err) {
                logger.error("Failed to delete " + dirPath + ":" + err);
                return;
            }
            //delete from database
            Project.deleteOne({ code: code }, function (err) {
                if (err) {
                    logger.error("Failed to delete project from DB " + code + ":" + err);
                }
            });
            CromwellJob.deleteOne({ project: code }, function (err) {
                if (err) {
                    logger.error("Failed to delete job from DB " + code + ":" + err);
                }
            });
        }
    });
}