const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const UserSchema = new Schema({
    firstname: {
        type: String,
        required: true
    },
    lastname: {
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true,
        unique: true
    },
    mailto: {
        type: String,
        required: false
    },
    notification: {
        type: String,
        default: "off",
        enum: ["on", "off"]
    },
    password: {
        type: String,
        required: true
    },
    googlepassword: {
        type: String,
        required: false
    },
    facebookpassword: {
        type: String,
        required: false
    },
    orcidpassword: {
        type: String,
        required: false
    },
    orcidtoken: {
        type: String,
        required: false
    },
    code: {
        type: String,
        required: true,
        unique: false
    },
    type: {
        type: String,
        default: "user"
    },
    status: {
        type: String,
        default: "inactive"
    },
    created: {
        type: Date,
        default: Date.now
    },
    updated: {
        type: Date,
        default: Date.now
    }
});

module.exports = User = mongoose.model("users", UserSchema);