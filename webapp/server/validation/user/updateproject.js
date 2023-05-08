const Validator = require("validator");
const isEmpty = require("is-empty");

module.exports = function validateUpdateprojectInput(data) {
    let errors = {};

    // Convert empty fields to an empty string so we can use validator functions
    data.code = !isEmpty(data.code) ? data.code : "";

    // Name checks
    if (Validator.isEmpty(data.code)) {
        errors[data.code] = "Project code is required";
    }

    return {
        errors,
        isValid: isEmpty(errors)
    };
};