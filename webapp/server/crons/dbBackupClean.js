const findRemoveSync = require('find-remove');
const config = require("../config");

const logger = require('../util/logger');

module.exports = function dbBackup() {
  logger.debug("Clean up DB backup");
  const result = findRemoveSync(config.DB.BACKUP_DIR, { dir: '^db-backup_', regex: true, age: { seconds: config.DB.BACKUP_LIFETIME_SECONDS } });
  logger.info(result);
}