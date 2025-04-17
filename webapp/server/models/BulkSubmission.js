const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const BulkSubmissionSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    desc: {
        type: String,
    },
    status: {
        type: String,
        default: "in queue",
        enum: ['in queue', 'failed', 'delete', 'rerun', 'complete', 'processing', 'submitted'],
    },
    type: {
        type: String,
        required: true
    },
    filename: {
        type: String,
        required: true
    },
    code: {
        type: String,
        required: true,
        unique: true
    },
    owner: {
        type: String,
        required: true
    },
    projects: [{
        type: String
    }],
    created: {
        type: Date,
        default: Date.now
    },
    updated: {
        type: Date,
        default: Date.now
    },
});

module.exports = BulkSubmission = mongoose.model("bulksubmissions", BulkSubmissionSchema);