const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const ProjectSchema = new Schema({
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
        enum: ['in queue', 'running', 'failed', 'delete', 'rerun', 'complete', 'processing', 'submitted'],
    },
    type: {
        type: String,
        required: true
    },
    code: {
        type: String,
        required: true,
        unique: true
    },
    public: {
        type: Boolean,
        default: false
    },
    notified: {
        type: Boolean,
        default: false
    },
    owner: {
        type: String,
        required: true
    },
    created: {
        type: Date,
        default: Date.now
    },
    updated: {
        type: Date,
        default: Date.now
    },
    sharedto: [{
        type: String
    }],
    metadatasubmissionid: {
        type: String,
        required: false
    }
});

module.exports = Project = mongoose.model("projects", ProjectSchema);