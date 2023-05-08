const Validator = require("validator");
const isEmpty = require("is-empty");

module.exports = function validateAdduploadInput(data) {
    let errors = {};

    // Convert empty fields to an empty string so we can use validator functions
    data.name = !isEmpty(data.name) ? data.name : "";
    data.type = !isEmpty(data.type) ? data.type : "";
    data.size = !isEmpty(data.size) ? data.size : "";

    // Name checks
    if (Validator.isEmpty(data.name)) {
        errors.name = "Name field is required";
    }
    if (Validator.isEmpty(data.type)) {
        errors.type = "Type field is required";
    }
    if (Validator.isEmpty(data.size)) {
        errors.size = "Size field is required";
    }
    
    return {
        errors,
        isValid: isEmpty(errors)
    };
};