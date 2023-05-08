const Validator = require("validator");
const isEmpty = require("is-empty");

module.exports = function validateAddprojectInput(data) {
    let errors = '';

    if (Validator.isEmpty(data.pipeline)) {
        errors += "Project type is required";
    }

    if (!data.project || !data.project.name || Validator.isEmpty(data.project.name)) {
        errors += "Project name is required";
    }
    
    return {
        errors,
        isValid: isEmpty(errors)
    };
};