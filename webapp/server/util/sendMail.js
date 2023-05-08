const nodemailer = require('nodemailer');
const mg = require('nodemailer-mailgun-transport');

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

        const service = process.env.SENDMAIL_SERVICE;
        let config = {};
        let transporter = null;
        if (process.env.SENDMAIL_PROXY) {
            config.proxy = process.env.SENDMAIL_PROXY;
        }
        if (service === 'mailgun') {
            config.auth = {
                api_key: process.env.SENDMAIL_USER,
                domain: process.env.SENDMAIL_PASS,
            }
            transporter = nodemailer.createTransport(mg(config));
        } else {
            config.auth = {
                user: process.env.SENDMAIL_USER,
                pass: process.env.SENDMAIL_PASS,
            }
            transporter = nodemailer.createTransport(config);
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
