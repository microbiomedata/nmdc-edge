const Validator = require("validator");
const isEmpty = require("is-empty");
const EmailValidator = require('email-deep-validator');

module.exports = async function validateRegisterInput(data) {
    let errors = {};

    // Convert empty fields to an empty string so we can use validator functions
    data.firstname = !isEmpty(data.firstname) ? data.firstname : "";
    data.lastname = !isEmpty(data.lastname) ? data.lastname : "";
    data.email = !isEmpty(data.email) ? data.email : "";
    data.password = !isEmpty(data.password) ? data.password : "";
    data.password2 = !isEmpty(data.password2) ? data.password2 : "";

    // Name checks
    if (Validator.isEmpty(data.firstname)) {
        errors.firstname = "First Name field is required";
    }
    if (Validator.isEmpty(data.lastname)) {
        errors.lastname = "Last Name field is required";
    }

    // Email checks
    if (Validator.isEmpty(data.email)) {
        errors.email = "Email field is required";
    } else if (!Validator.isEmail(data.email)) {
        errors.email = "Email is invalid";
    } else {
        const emailValidator = new EmailValidator();
        const { wellFormed, validDomain, validMailbox } = await emailValidator.verify(data.email);
        //console.log("deep email", validDomain, validMailbox)
        if(validDomain === false || validMailbox === false) {
            errors.email = "Email is invalid";
        }
    }

    // Password checks
    if (Validator.isEmpty(data.password)) {
        errors.password = "Password field is required";
    }
    if (Validator.isEmpty(data.password2)) {
        errors.password2 = "Confirm password field is required";
    }
    if (!Validator.isLength(data.password, { min: 8, max: 30 })) {
        errors.password = "Password must be at least 8 characters";
    }
    if (!Validator.equals(data.password, data.password2)) {
        errors.password2 = "Passwords must match";
    }
    
    return {
        errors,
        isValid: isEmpty(errors)
    };
};