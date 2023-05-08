const fs = require('fs');
const moment = require('moment');
const Project = require("../models/Project");
const CromwellJob = require("../models/CromwellJob");
const logger = require('../util/logger');

module.exports = function projectMonitor() {
    logger.debug("project monitor");

    //delete file after deleteGracePeriod 
    const deleteGracePeriod = moment().subtract(process.env.PROJECT_DELETE_GRACE_PERIOD, 'days');
    Project.find({ 'status': 'delete', 'updated': { '$lte': deleteGracePeriod } }).then(projs => {
        var i;
        for (i = 0; i < projs.length; i++) {
            const code = projs[i].code;
            logger.info("delete project: " + code)
            const path = process.env.PROJECT_HOME + "/" + code;
            // delete directory recursively
            try {
                fs.rmdirSync(path, { recursive: true });
                logger.info("deleted " + path);
            } catch (err) {
                logger.error("Failed to delete " + path + ":" + err);
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