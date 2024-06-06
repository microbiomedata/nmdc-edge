const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const OrcidUserSchema = new Schema({
    orcidid: {
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true
    },
    created: {
        type: Date,
        default: Date.now
    }
});

module.exports = OrcidUser = mongoose.model("OrcidUsers", OrcidUserSchema);