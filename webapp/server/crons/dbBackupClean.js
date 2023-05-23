const findRemoveSync = require('find-remove');

const logger = require('../util/logger');

module.exports = function dbBackup() {
  logger.debug("Clean up DB backup");
  const result = findRemoveSync(process.env.DB_BACKUP_DIR, { dir: '^db-backup_', regex: true, age: { seconds: process.env.DB_BACKUP_CLEAN_AGE_INSECONDES } });
  logger.info(result);
}