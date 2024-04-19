const nodemailer = require('nodemailer');
const mg = require('nodemailer-mailgun-transport');
const config = require("../config");

module.exports = function sendMail(from, recipient, message) {
    return new Promise((resolve, reject) => {
        const data = {
            from: from,
            to: recipient,
            subject: message.subject,
        };
        if (message.text) {
            data.text = message.text;
        }
        if (message.html) {
            data.html = message.html;
        }

        const service = config.EMAIL.SERVICE_IDENTIFIER;
        let transporterConfig = {};
        let transporter = null;
        if (typeof config.EMAIL.SERVICE_PROXY_URL === "string" && config.EMAIL.SERVICE_PROXY_URL.length > 0) {
            transporterConfig.proxy = config.EMAIL.SERVICE_PROXY_URL;
        }
        if (service === 'mailgun') {
            transporterConfig.auth = {
                domain: config.EMAIL.MAILGUN_DOMAIN,
                api_key: config.EMAIL.MAILGUN_API_KEY, 
            }
            transporter = nodemailer.createTransport(mg(transporterConfig));
        } else {
            transporterConfig.auth = {
                user: config.EMAIL.SERVICE_USERNAME,
                pass: config.EMAIL.SERVICE_PASSWORD,
            }
            transporter = nodemailer.createTransport(transporterConfig);
        }

        transporter.sendMail(data, function (error, info) {
            if (error) {
                return reject(error);
            } else {
                resolve();
            }
        });
    });
};
