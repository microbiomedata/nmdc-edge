const Validator = require("validator");
const isEmpty = require("is-empty");

module.exports = function validateSendmail(data) {
    let errors = {};

    // Convert empty fields to an empty string so we can use validator functions
    data.to = !isEmpty(data.to) ? data.to : "";

    // Email checks
    if (Validator.isEmpty(data.to)) {
        errors.to = "Email field is required";
    } else if (!Validator.isEmail(data.to)) {
        errors.to = "Email is invalid";
    }
    
    return {
        errors,
        isValid: isEmpty(errors)
    };
};