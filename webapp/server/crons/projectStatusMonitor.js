const fs = require('fs');
const Project = require("../models/Project");
const User = require("../models/User");
const logger = require('../util/logger');
const sendMail = require('../util/sendMail');
const tmpl = process.env.PROJECT_STATUS_TEMPLATE;

module.exports = function projectMonitor() {
    logger.debug("project status monitor");

    //notify complete/failed projects
    Project.find({ 'notified': false }).then(projs => {
        projs.forEach(proj => {
            if (process.env.SENDMAIL_PROJECT === 'on') {
                if (proj.status === 'complete' || proj.status === 'failed') {
                    User.findOne({ email: proj.owner }).then(user => {
                        if (!user) {
                            logger.debug("User not found: " + proj.owner);
                        } else {
                            if (user.notification === 'on') {
                                let projectLink = "<a href='" + process.env.PROJECT_URL + proj.code + "'>View Project</a>";

                                let projectTmpl = String(fs.readFileSync(tmpl));
                                projectTmpl = projectTmpl.replace(/PROJECTNAME/g, proj.name);
                                projectTmpl = projectTmpl.replace(/PROJECTDESC/g, proj.desc);
                                projectTmpl = projectTmpl.replace(/PROJECTSTATUS/g, proj.status);
                                projectTmpl = projectTmpl.replace(/PROJECTTYPE/g, proj.type);
                                projectTmpl = projectTmpl.replace(/PROJECTLINK/g, projectLink);

                                let message = { subject: "NMDC EDGE Project Status", html: projectTmpl };
                                //call sendmail
                                sendMail(process.env.SENDMAIL_FROM, user.mailto, message).then(status => {
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