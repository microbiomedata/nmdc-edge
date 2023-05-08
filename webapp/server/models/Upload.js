const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const UploadSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    desc: {
        type: String,
    },
    size: {
        type: Number,
        required: true
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
    status: {
        type: String,
        default: "live",
        enum: ['live', 'delete'],
    },
    public: {
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
    }]
});

module.exports = Upload = mongoose.model("upload", UploadSchema);