const { exec } = require("child_process");
const moment = require('moment');
const config = require("../config");

const logger = require('../util/logger');

module.exports = function dbBackup() {
  logger.debug("DB backup");
  // mongodump
  const dateStringWithTime = moment(new Date()).format('YYYY-MM-DD:HH:mm');
  const cmd = `mongodump --db ${config.DB.DATABASE_NAME} --out ${config.DB.BACKUP_DIR}/db-backup_${dateStringWithTime}`;

  logger.info(cmd);
  //run local
  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      logger.error(error.message);
    }
    if (stderr) {
      logger.error(stderr);
    }
  });
}