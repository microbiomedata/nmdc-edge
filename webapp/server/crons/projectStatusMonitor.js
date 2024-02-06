const fs = require('fs');
const Project = require("../models/Project");
const User = require("../models/User");
const logger = require('../util/logger');
const sendMail = require('../util/sendMail');
const config = require("../config");
const tmpl = config.EMAIL.PROJECT_STATUS_EMAIL_TEMPLATE_PATH;

module.exports = function projectMonitor() {
    logger.debug("project status monitor");

    //notify complete/failed projects
    Project.find({ 'notified': false }).then(projs => {
        projs.forEach(proj => {
            if (config.EMAIL.SEND_PROJECT_STATUS_EMAILS === true) {
                if (proj.status === 'complete' || proj.status === 'failed') {
                    User.findOne({ email: proj.owner }).then(user => {
                        if (!user) {
                            logger.debug("User not found: " + proj.owner);
                        } else {
                            if (user.notification === 'on') {
                                let projectLink = "<a href='" + config.APP.EXTERNAL_BASE_URL + '/user/project?code=' + proj.code + "'>View Project</a>";

                                let projectTmpl = String(fs.readFileSync(tmpl));
                                projectTmpl = projectTmpl.replace(/PROJECTNAME/g, proj.name);
                                projectTmpl = projectTmpl.replace(/PROJECTDESC/g, proj.desc);
                                projectTmpl = projectTmpl.replace(/PROJECTSTATUS/g, proj.status);
                                projectTmpl = projectTmpl.replace(/PROJECTTYPE/g, proj.type);
                                projectTmpl = projectTmpl.replace(/PROJECTLINK/g, projectLink);

                                let message = { subject: "NMDC EDGE Project Status", html: projectTmpl };
                                //call sendmail
                                sendMail(config.EMAIL.FROM_ADDRESS, user.mailto, message).then(status => {
                                    logger.debug("project status notification sent out.");
                                }).catch(err => {
                                    logger.error("sendmail: " + err);
                                });
                            }
                        }
                    }).catch(function (err) {
                        logger.error(err);
                    });
                    proj.notified = true;
                    proj.updated = Date.now();
                    proj.save();
                }
            } else {
                proj.notified = true;
                proj.updated = Date.now();
                proj.save();
            }
        });
    });
}