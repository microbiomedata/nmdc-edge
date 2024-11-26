const express = require("express");
const router = express.Router();
const bcrypt = require("bcryptjs");
const randomize = require('randomatic');
const sendMail = require('../../util/sendMail');
const logger = require('../../util/logger');
const dbsanitize = require('mongo-sanitize');
const config = require("../../config");

// Load input validation
const validateRegisterInput = require("../../validation/user/register");
const validateLoginInput = require("../../validation/user/login");
const validateSocialLogin = require("../../validation/user/sociallogin");
const validateActivateInput = require("../../validation/user/activate");
const validateEmail = require("../../validation/user/email");
const validateResetpasswordInput = require("../../validation/user/resetpassword");
const validateSendmail = require("../../validation/user/sendmail");

// Load User model
const User = require("../../models/User");
const common = require("../common");

const sysError = "API server error";

// @route POST api/user/sendmail
// @access Public
router.post("/sendmail", (req, res) => {
    logger.debug("/api/user/sendmail: " + JSON.stringify(req.body));
    const { errors, isValid } = validateSendmail(req.body);

    // Check validation
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json("Invalid sendmail request.");
    }

    if (req.body.token !== config.EMAIL.SHARED_SECRET) {
        logger.debug("sendmail: Permission denied");
        return res.status(400).json("Permission denied.");
    }

    User.findOne({ email: dbsanitize(req.body.to) }).then(user => {
        if (user === null) {
            logger.error("sendmail: The recipient is invalid." + req.body.to);
            return res.status(400).json("The recipient is invalid.");
        }

        //call sendmail
        sendMail(config.EMAIL.FROM_ADDRESS, req.body.to, req.body.message).then(status => {
            return res.json({ sendmail: "success" });
        }).catch(err => {
            logger.error("sendmail: " + err);
            return res.status(400).json(sysError + ": sendmail failed");
        });
    }).catch(err => { logger.error("sendmail: " + err); return res.status(500).json(sysError); });
});

// @route POST api/user/register
// @desc Register user
// @access Public
router.post("/register", async (req, res) => {
    // Form validation
    const { errors, isValid } = await validateRegisterInput(req.body);
    // Check validation
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json(errors);
    }
    logger.debug("/api/user/register: " + JSON.stringify(req.body.email));

    User.findOne({ email: req.body.email }).then(user => {
        if (user) {
            logger.error("register: Email already exists." + req.body.email);
            return res.status(400).json({ email: "Email already exists" });
        } else {
            var code = randomize("0", 6);
            const newUser = new User({
                firstname: req.body.firstname,
                lastname: req.body.lastname,
                email: req.body.email,
                mailto: req.body.email,
                password: req.body.password,
                status: req.body.status,
                code: code
            });
            // Hash password before saving in database
            common.encodePassword(newUser.password).then(hash => {
                newUser.password = hash;
                newUser.save().then(user => {
                    return res.json({ user: user, mail_token: config.EMAIL.SHARED_SECRET })
                }).catch(err => {
                    logger.error("register: " + err);
                    return res.status(500).json(sysError);
                });
            }).catch(err => {
                logger.error("register: " + err);
                return res.status(500).json(sysError);
            });
        }
    }).catch(err => {
        logger.error("register: " + err); return res.status(500).json(sysError);
    });
});

// @route POST api/user/activate
// @desc status user account
// @access Public
router.post("/activate", (req, res) => {
    logger.debug("/api/user/activate: " + JSON.stringify(req.body));
    // Form validation
    const { errors, isValid } = validateActivateInput(req.body);
    // Check validation
    if (!isValid) {
        logger.error("activate: " + errors);
        return res.status(400).json({ activate: "Invalid token." });
    }
    const email = dbsanitize(req.body.email);
    const password = req.body.password;

    // Find user by email
    User.findOne({ email: email }).then(user => {
        // Check if user exists
        if (user === null) {
            logger.error("activate: Account not found." + email);
            return res.status(400).json({ activate: "Account not found," });
        }

        if (user.status === "active") {
            logger.error("activate: Account has already been activated." + email);
            return res.status(400).json({ activate: "Your account has already been activated." });
        }

        if (user.password === password) {
            // User matched
            User.updateOne({ email: email }, { status: "active" }, (err) => {
                if (err) {
                    logger.error("activate: Faile to update user status: " + err);
                    return res
                        .status(500)
                        .json(sysError);
                } else {
                    const payload = {
                        id: user.id,
                        firstname: user.firstname,
                        lastname: user.lastname,
                        type: user.type,
                        status: user.status,
                        code: user.code
                    };
                    return res.json({ user: payload })
                }
            });
        } else {
            logger.error("activate: Invalid token");
            return res.status(400).json({ activate: "Invalid token." });
        }
    }).catch(err => { logger.error("activate: " + err); return res.status(500).json(sysError); });
});

// @route POST api/user/getActivationLink
// @desc active user account
// @access Public
router.post("/getActivationLink", (req, res) => {
    logger.debug("/api/user/getActivationLink: " + JSON.stringify(req.body));
    const { errors, isValid } = validateEmail(req.body);

    // Check validation
    if (!isValid) {
        logger.error("getActivationLink: " + errors);
        return res.status(400).json({ activate: "Invalid email." });
    }

    const email = dbsanitize(req.body.email);

    // Find user by email
    User.findOne({ email: email }).then(user => {
        // Check if user exists
        if (user === null) {
            logger.error("getActivationLink: Account not found." + email);
            return res.status(400).json({ activate: "Account not found." });
        }

        if (user.status === "active") {
            logger.error("getActivationLink: Account has already been activated." + email)
            return res.status(400).json({ activate: "Your account has already been activated." });
        }

        return res.json({ user: { email: user.email, password: user.password }, mail_token: config.EMAIL.SHARED_SECRET });
    }).catch(err => { logger.error("getActivationLink: " + err); return res.status(500).json(sysError); });
});

// @route POST api/user/resetpassword
// @desc active user account
// @access Public
router.post("/resetpassword", (req, res) => {
    logger.debug("/api/user/resetpassword: " + JSON.stringify(req.body));
    // Form validation
    const { errors, isValid } = validateResetpasswordInput(req.body);

    // Check validation
    if (!isValid) {
        logger.error(errors);
        return res.status(400).json({ resetpassword: "Invalid token." });
    }
    const email = dbsanitize(req.body.email);
    const password = req.body.password;
    const newpassword = req.body.newpassword;

    // Find user by email
    User.findOne({ email: email }).then(user => {
        // Check if user exists
        if (user === null) {
            logger.error("resetpassword: Account not found." + email);
            return res.status(400).json({ resetpassword: "Account not found." });
        }
        if (user.status !== "active") {
            logger.error("resetpassword: Account is not active." + email);
            return res.status(400).json({ resetpassword: "Your account is not active." });
        }

        if (user.password === password) {
            // Hash password before saving in database
            common.encodePassword(newpassword).then(hash => {
                //change code
                let code = randomize("0", 6);
                User.updateOne({ email: email }, { password: hash }, { code: code }, (err) => {
                    if (err) {
                        logger.error("resetpassword: Faile to update user password: " + err);
                        return res.status(500).json(sysError);
                    } else {
                        const payload = {
                            id: user.id,
                            email: user.email,
                        };
                        return res.json({ user: payload })
                    }
                });
            }).catch(err => {
                logger.error("register: " + err);
                return res.status(500).json(sysError);
            });
        } else {
            return res.status(400).json({ resetpassword: "Invalid token." });
        }
    }).catch(err => { logger.error("resetpassword: " + err); return res.status(500).json(sysError); });
});

// @route POST api/user/getResetpasswordLink
// @desc active user account
// @access Public
router.post("/getResetpasswordLink", (req, res) => {
    logger.debug("/api/user/getResetpasswordLink: " + JSON.stringify(req.body));
    const { errors, isValid } = validateEmail(req.body);

    // Check validation
    if (!isValid) {
        if (debug) console.log(errors);
        return res.status(400).json({ resetpasswordLink: "Invalid email." });
    }

    const email = dbsanitize(req.body.email);

    // Find user by email
    User.findOne({ email: email }).then(user => {
        // Check if user exists
        if (user === null) {
            logger.error("resetpasswordLink: Account not found." + email);
            return res.status(400).json({ resetpasswordLink: "Account not found" });
        }
        if (user.status !== "active") {
            logger.error("resetpasswordLink: Account not active." + email);
            return res.status(400).json({ resetpasswordLink: "Your account is not active." });
        }

        return res.json({ user: { email: user.email, password: user.password }, mail_token: config.EMAIL.SHARED_SECRET });
    }).catch(err => {
        logger.error("resetpasswordLink: " + err);; return res.status(500).json(sysError);
    });
});

// @route POST api/user/login
// @desc Login user and return JWT token
// @access Public
router.post("/login", (req, res) => {
    // Form validation
    const { errors, isValid } = validateLoginInput(req.body);
    // Check validation
    if (!isValid) {
        return res.status(400).json(errors);
    }
    logger.debug("/api/user/login: " + JSON.stringify(req.body.email));
    const email = dbsanitize(req.body.email);
    const password = req.body.password;
    // Find user by email
    User.findOne({ email: email }).then(user => {
        // Check if user exists
        if (!user) {
            logger.error("login: Email not found." + email)
            return res.status(400).json({ email: "Email not found" });
        }
        // Check status
        if (user.status !== "active") {
            logger.error("login: Email not active." + email)
            return res.status(400).json({ email: "Your account is not active" });
        }
        // Check password
        bcrypt.compare(password, user.password).then(isMatch => {
            if (isMatch) {
                // User matched
                // Create JWT Payload
                const payload = {
                    id: user.id,
                    firstname: user.firstname,
                    lastname: user.lastname,
                    email: user.email,
                    mailto: user.mailto,
                    notification: user.notification,
                    type: user.type,
                    status: user.status,
                    code: user.code
                };
                // Sign token
                common.signToken(payload).then(token => {
                    return res.json({
                        success: true,
                        token: "Bearer " + token
                    });
                }
                ).catch(err => {
                    logger.error("login: Failed to generate a jwt token: " + err);
                    return res.status(500).json(sysError);
                });
            } else {
                logger.error("login: Password incorrect." + email)
                return res.status(400).json({ password: "Password incorrect" });
            }
        });
    }).catch(err => { logger.error("login: " + err); return res.status(500).json(sysError); });
});

// @route POST api/user/sociallogin
// @desc Login user and return JWT token
// @access Public
router.post("/sociallogin", (req, res) => {
    // Form validation
    const { errors, isValid } = validateSocialLogin(req.body);
    // Check validation
    if (!isValid) {
        return res.status(400).json(errors);
    }
    logger.debug("/api/user/sociallogin: " + JSON.stringify(req.body.email));
    const email = dbsanitize(req.body.email);
    const password = req.body.password + config.AUTH.OAUTH_SECRET;
    const socialType = req.body.socialtype;

    common.encodePassword(password).then(hash => {
        // Find user by email
        User.findOne({ email: email }).then(user => {
            if (!user) {
                logger.info("Create account from social login " + email);
                var code = randomize("0", 6);

                const newUser = new User({
                    firstname: req.body.firstname,
                    lastname: req.body.lastname,
                    email: req.body.email,
                    status: req.body.status,
                    code: code,
                    orcidtoken: req.body.orcid_token
                });

                newUser.password = hash;

                if (socialType === 'google') {
                    newUser.googlepassword = hash;
                } else if (socialType === 'facebook') {
                    newUser.facebookpassword = hash;
                } else if (socialType === 'orcid') {
                    newUser.orcidpassword = hash;
                }

                newUser.save().then(user => {
                    logger.debug("New user: " + user.email);
                    if (user.status === 'inactive') {
                        return res.json({ user: user, mail_token: config.EMAIL.SHARED_SECRET });
                    } else {
                        // Create JWT Payload
                        const payload = {
                            id: user.id,
                            firstname: user.firstname,
                            lastname: user.lastname,
                            email: user.email,
                            mailto: user.mailto,
                            notification: user.notification,
                            type: user.type,
                            socialtype: socialType,
                            status: user.status,
                            code: user.code
                        };
                        common.signToken(payload).then(token => {
                            return res.json({
                                success: true,
                                token: "Bearer " + token
                            });
                        }).catch(err => { logger.error("sign token sociallogin: " + err); return res.status(500).json(sysError); });

                    }
                }).catch(err => {
                    logger.error("Failed to register social account: " + err);
                    return res.status(500).json(sysError);
                });

            } else {
                // Create JWT Payload
                const payload = {
                    id: user.id,
                    firstname: user.firstname,
                    lastname: user.lastname,
                    email: user.email,
                    mailto: user.mailto,
                    notification: user.notification,
                    type: user.type,
                    socialtype: socialType,
                    status: user.status,
                    code: user.code
                };
                let update = false;
                if (socialType === 'google' && !user.googlepassword) {
                    //user already registered with this email, update user
                    user.googlepassword = hash;
                    update = true;
                }
                if (socialType === 'facebook' && !user.facebookpassword) {
                    //user already registered with this email, update user
                    user.facepassword = hash;
                    update = true;
                }
                if (socialType === 'orcid' && !user.orcidpassword) {
                    //user already registered with this email, update user
                    user.orcidpassword = hash;
                    update = true;
                }
                if (req.body.orcid_token) {
                    user.orcidtoken = req.body.orcid_token;
                    update = true;
                }
                if (update === true) {
                    user.save().then(user => {
                        logger.debug("Update user: " + user.email);

                        if (user.status === 'inactive') {
                            return res.json({ user: user, mail_token: config.EMAIL.SHARED_SECRET });
                        } else {
                            common.signToken(payload).then(token => {
                                return res.json({
                                    success: true,
                                    token: "Bearer " + token
                                });
                            }).catch(err => { logger.error("sociallogin: " + err); return res.status(500).json(sysError); });

                        }
                    }).catch(err => {
                        logger.error("Failed to update social account: " + err);
                        return res.status(500).json(sysError);
                    });
                } else {
                    let socialPassword = user.googlepassword;
                    if (socialType === 'facebook') {
                        socialPassword = user.facebookpassword;
                    } else if (socialType === 'orcid') {
                        socialPassword = user.orcidpassword;
                    }
                    // Check password
                    bcrypt.compare(password, socialPassword).then(isMatch => {
                        if (isMatch) {
                            // User matched
                            if (user.status === 'inactive') {
                                return res.json({ user: user, mail_token: config.EMAIL.SHARED_SECRET });
                            } else {
                                common.signToken(payload).then(token => {
                                    return res.json({
                                        success: true,
                                        token: "Bearer " + token
                                    });
                                }).catch(err => { logger.error("sociallogin: " + err); return res.status(500).json(sysError); });

                            }
                        } else {
                            logger.error("sociallogin: Password incorrect." + email)
                            return res.status(400).json({ sociallogin: "Password incorrect" });
                        }
                    });
                }
            }
        }).catch(err => { logger.error("sociallogin: " + err); return res.status(500).json(sysError); });

    }).catch(err => { logger.error("hash sociallogin: " + err); return res.status(500).json(sysError); });
});

module.exports = router;