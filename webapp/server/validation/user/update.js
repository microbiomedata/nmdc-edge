const Validator = require("validator");
const isEmpty = require("is-empty");

module.exports = function validateUpdateInput(data) {
    let errors = {};

    // Convert empty fields to an empty string so we can use validator functions
    data.firstname = !isEmpty(data.firstname) ? data.firstname : "";
    data.lastname = !isEmpty(data.lastname) ? data.lastname : "";
    data.password = !isEmpty(data.password) ? data.password : "";
    data.password2 = !isEmpty(data.password2) ? data.password2 : "";

    // Name checks
    if (Validator.isEmpty(data.firstname)) {
        errors.firstname = "First Name field is required";
    }
    if (Validator.isEmpty(data.lastname)) {
        errors.lastname = "Last Name field is required";
    }

    // Password checks
    if (!Validator.isEmpty(data.password)) {
        if (!Validator.isLength(data.password, { min: 8, max: 30 })) {
            errors.password = "Password must be at least 8 characters";
        }
        if (!Validator.equals(data.password, data.password2)) {
            errors.password2 = "Passwords must match";
        }
    }
    
    return {
        errors,
        isValid: isEmpty(errors)
    };
};