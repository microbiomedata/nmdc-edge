/**
 * This is a PM2 configuration file.
 *
 * Note: This file is based upon a file formerly in the repository, named `webapp/installation/server_pm2.tmpl`.
 *       I am documenting that history here so contributors familiar with the former file know the relationship.
 *
 * References:
 * - https://pm2.keymetrics.io/docs/usage/application-declaration/
 * - https://pm2.keymetrics.io/docs/usage/environment/
 */

module.exports = {
    apps: [
        {
            name: "server", // TODO: Rename to "webserver" in order to be consistent with the name, "cronserver," below.
            script: "server.js",
            instances: 4,
            exec_mode: "cluster",
            cwd: "./webapp/server",
            node_args: "--max_old_space_size=1024",
            max_memory_restart: "150M"
        },
        {
            name: "cronserver",
            script: "cronserver.js",
            cwd: "./webapp/server",
            node_args: "--max_old_space_size=1024",
            max_memory_restart: "150M"
        }
    ]
}
