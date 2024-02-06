const fs = require('fs');
const path = require("path");
const config = require("../config");

const { generateWorkflowResult, generatePipelineResult, generateRunStats } = require("./workflow");

// //BioAI
// const getResult = function (project) {
//     const proj_home = path.join(config.PROJECTS.BASE_DIR, project.code);
//     const result_json = proj_home + "/bioai_out.json";

//     return JSON.parse(fs.readFileSync(result_json));
// }

const getResult = function (project) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, project.code);
    const result_json = proj_home + "/result.json";

    if (!fs.existsSync(result_json)) {
        if (project.type.match(/Pipeline$/)) {
            generatePipelineResult(project);
        } else {
            generateWorkflowResult(project);
        }
    }
    return JSON.parse(fs.readFileSync(result_json));
}

const getRunStats = function (project) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, project.code);
    const stats_json = proj_home + "/run_stats.json";
    generateRunStats(project);
    return JSON.parse(fs.readFileSync(stats_json));
}

const getConf = function (project) {
    const proj_home = path.join(config.PROJECTS.BASE_DIR, project.code);
    const conf_json = proj_home + "/conf.json";
    return JSON.parse(fs.readFileSync(conf_json));
}


module.exports = { getResult, getRunStats, getConf }