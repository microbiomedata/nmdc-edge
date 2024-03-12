/**
 * Configure the app based upon environment variables.
 *
 * This module acts as an interface between the process environment variables (i.e. `process.env.*`)
 * and the modules that consume their values. This (a) facilitates validation of their values and
 * the assignment of default/fallback values; and (b) reduces the number of occurrences of `process.env.*`
 * variables throughout the codebase, which can be sources of errors as some IDEs do not validate their
 * existence during development, since, at that time, they do not exist as JavaScript symbols.
 *
 * References:
 * - https://nodejs.org/en/learn/command-line/how-to-read-environment-variables-from-nodejs
 * - https://developer.mozilla.org/en-US/docs/Glossary/Falsy
 */

/**
 * Returns the value resolved to an integer; or `undefined` if the original value is `undefined`.
 *
 * References: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/parseInt
 *
 * Examples:
 * f("123")     => 123
 * f("xyz")     => NaN (which is a Falsy value)
 * f(undefined) => undefined
 *
 * @param val {string|undefined} The value you want to resolve to an integer
 * @return {number|undefined} The integer, or `undefined`
 */
const makeIntIfDefined = (val) => {
    return typeof val === "string" ? parseInt(val, 10) : undefined;
};

/**
 * Returns an Array of the file extension strings specified via the delimited string.
 *
 * Examples:
 * - f("pdf|zip|c", "|") => ["pdf", "zip", "c"]
 *
 * @param delimitedStr
 * @param delimiter
 * @return {string[]}
 */
const makeFileExtensionArray = (delimitedStr = "", delimiter = "|") => {
    return typeof delimitedStr === "string" ? delimitedStr.split(delimiter) : [];
}

/**
 * Returns `true` if the value matches "true" (ignoring letter casing); otherwise, returns `false`.
 *
 * Examples:
 * - f("TrUe") => true
 * - f("1")    => false
 *
 * @param val {string} The string you want to resolve to a Boolean value
 * @return {boolean} The Boolean value
 */
const makeBoolean = (val = "") => {
    return typeof val === "string" ? (/^true$/i).test(val) : false;
};

/**
 * Returns a local URI based upon the specified parameters; and the current protocol and domain.
 *
 * References:
 * - https://developer.mozilla.org/en-US/docs/Web/API/Location/protocol
 * - https://developer.mozilla.org/en-US/docs/Web/API/Location/host
 *
 * @param pathWithLeadingSlash {string} The path portion of the URI, including the leading forward slash
 * @return {string} The resulting local URI
 */
const makeLocalUri = (pathWithLeadingSlash = "/") => {
    const protocol = window.location.protocol; // e.g. "http:" or "https:"
    const host = window.location.host; // e.g. "www.example.com" or "www.example.com:1234"
    return `${protocol}//${host}${pathWithLeadingSlash}`;
};

/**
 * Returns an ORCiD Auth URI based upon the specified parameters.
 *
 * References:
 * - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent
 *
 * @param redirectUri {string} URI to which you want ORCiD to redirect the client after authenticating
 * @param orcidClientId {string} ORCiD `client_id` obtained from the ORCiD Developer Tools web page
 * @param nonceVal {string} Nonce value we can use to verify that the redirected client originated here
 * @param orcidAuthBaseUri {string} ORCiD oAuth base URI
 * @return {string} The resulting ORCiD Auth URI
 */
const makeOrcidAuthUri = (redirectUri, orcidClientId, nonceVal = "whatever", orcidAuthBaseUri = "https://orcid.org/oauth/authorize") => {
    const sanitizedRedirectUri = encodeURIComponent(redirectUri);
    const sanitizedOrcidClientId = encodeURIComponent(orcidClientId);
    const sanitizedNonceVal = encodeURIComponent(nonceVal);
    return `${orcidAuthBaseUri}?response_type=token&redirect_uri=${sanitizedRedirectUri}&client_id=${sanitizedOrcidClientId}&scope=openid&nonce=${sanitizedNonceVal}`;
}

const config = {
    APP: {
        // The user-facing name of the application.
        NAME: `NMDC EDGE`,
    }, API: {
        // Base URI at which visitors can access the application.
        // Note: This is written under the assumption that the client and API server share a domain.
        BASE_URI: process.env.REACT_APP_API_URL || makeLocalUri("/"),
    }, ORCID: {
        // Boolean flag indicating whether the client will offer ORCiD-based authentication.
        IS_ENABLED: makeBoolean(process.env.REACT_APP_IS_ORCID_AUTH_ENABLED) || false,
        // ORCiD Auth URI, which contains the ORCiD Client ID.
        // Note: You can get the ORCiD Client ID value from: https://orcid.org/developer-tools
        AUTH_URI: makeOrcidAuthUri(makeLocalUri("/oauth"), process.env.REACT_APP_ORCID_CLIENT_ID),
    }, EMAIL: {
        // Boolean flag indicating whether the client will request that the server send emails to the user.
        IS_ENABLED: makeBoolean(process.env.REACT_APP_IS_EMAIL_NOTIFICATION_ENABLED) || false,
        // Strings that are incorporated into the user registration email.
        // TODO: Define these strings on the server side, not the client side.
        REGISTRATION: {
            SUBJECT: `Your NMDC EDGE account`,
            MESSAGE: `Thanks for using NMDC EDGE! Please activate your account at: ${makeLocalUri("/activate")}`,
        },
        // Strings that are incorporated into the password reset email.
        // TODO: Define these strings on the server side, not the client side.
        PASSWORD_RESET: {
            SUBJECT: `Reset your NMDC EDGE password`,
            MESSAGE: `Someone requested a password reset for your NMDC EDGE account. If this was not you, you can disregard this email. Otherwise, you can reset your password by visiting: ${makeLocalUri("/resetpassword")}`,
        },
    }, UPLOADS: {
        // List of file extensions of the files the client will allow users to upload.
        // Note: The environment variable, if defined, will contain a pipe-delimited string (e.g. "fastq|fq|faa"),
        //       whereas the resulting config variable will contain an array of strings (e.g. ["fastq", "fq", "faa"]).
        ALLOWED_FILE_EXTENSIONS: typeof process.env.REACT_APP_ALLOWED_FILE_EXTENSIONS_FOR_UPLOAD === "string" ?
            makeFileExtensionArray(process.env.REACT_APP_ALLOWED_FILE_EXTENSIONS_FOR_UPLOAD) :
            ["fastq", "fq", "faa", "fa", "fasta", "fna", "contigs", "fastq.gz", "fq.gz", "fa.gz", "fasta.gz", "fna.gz", "contigs.gz", "fa.bz2", "fasta.bz2", "contigs.bz2", "fna.bz2", "fa.xz", "fasta.xz", "contigs.xz", "fna.xz", "gbk", "gff", "genbank", "gb", "xlsx", "txt", "bed", "config", "tsv", "csv", "raw", "d", "bam", "sam"],
    }, DOWNLOADS: {
        // Maximum size of folder (in Bytes) the client will allow visitors to download.
        // Note: 1610612740 Bytes is 1.5 Gibibytes (1.6 Gigabytes).
        // Reference: https://www.xconvert.com/unit-converter/bytes-to-gigabytes
        MAX_FOLDER_SIZE_BYTES: makeIntIfDefined(process.env.REACT_APP_FOLDER_DOWNLOAD_MAX_SIZE) || 1610612740,
    }
};

export default config;