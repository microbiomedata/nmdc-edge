const mongoose = require("mongoose");
const Schema = mongoose.Schema;

// Create Schema
const CromwellJobSchema = new Schema({
    id: {
        type: String,
        required: false,
        unique: true
    },
    project: {
        type: String,
        required: true,
        unique: true
    },
    type: {
        type: String,
        //required: true
    },
    inputsize: {
        type: Number,
        default: 0
    },
    status: {
        type: String,
        default: "Submitted",
        enum: ['Submitted', 'Running', 'Failed', 'Aborted', 'Succeeded'],
    },
    updated: {
        type: Date,
        default: Date.now
    },
});

module.exports = CromwellJob = mongoose.model("cromwelljobs", CromwellJobSchema);