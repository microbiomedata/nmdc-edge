/**
 * This module exposes values from `process.env` in a way that facilitates IDE code completion
 * in consuming modules.
 */

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
 * - https://developer.mozilla.org/en-US/docs/Web/API/Location/hostname
 * - https://developer.mozilla.org/en-US/docs/Web/API/Location/port
 *
 * @param path {string} The path portion of the URI, including the leading forward slash
 * @return {string} The resulting local URI
 */
const makeLocalUri = (path = "") => {
    const protocol = window.location.protocol; // e.g. "http:" or "https:"
    const domain = window.location.hostname; // e.g. "www.example.com"
    const port = window.location.port; // e.g. "8000" or "80" or ""
    const portIfAny = port === "" ? "" : `:${port}`;
    return `${protocol}//${domain}${portIfAny}${path}`;
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

/**
 * Extracts and returns the specified query parameter value from the specified URI.
 *
 * References:
 * - https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams/URLSearchParams
 * - https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams/get
 *
 * @param uri {string} The URI containing the query string containing the specified parameter
 * @param paramName {string} Name of the parameter whose value you want to extract
 * @return {string} The extracted parameter value
 */

const config = {
    APP: {
        NAME: `NMDC EDGE`,
    },
    API: {
        // Note: This is written under the assumption that the client and API server share a domain.
        BASE_URI: makeLocalUri(),
    },
    ORCID: {
        IS_ENABLED: makeBoolean(process.env.REACT_APP_IS_ORCID_AUTH_ENABLED),
        AUTH_URI: makeOrcidAuthUri(makeLocalUri("/oauth"), process.env.REACT_APP_ORCID_CLIENT_ID),
    },
    EMAIL: {
        IS_ENABLED: makeBoolean(process.env.REACT_APP_IS_EMAIL_NOTIFICATION_ENABLED),
        // TODO: Define these messages on the server side, not the client side.
        REGISTRATION: {
            SUBJECT: `Your NMDC EDGE account`,
            MESSAGE: `Thanks for using NMDC EDGE! Please activate your account at: makeLocalUri("/activate")`,
        },
        // TODO: Define these messages on the server side, not the client side.
        PASSWORD_RESET: {
            SUBJECT: `Reset your NMDC EDGE password`,
            MESSAGE: `Someone requested a password reset for your NMDC EDGE account. If this was not you, you can disregard this email. Otherwise, you can reset your password by visiting: ${makeLocalUri("/resetpassword")}`,
        },
    },
    UPLOAD: {
        ALLOWED_FILE_EXTENSIONS: makeFileExtensionArray(process.env.REACT_APP_ALLOWED_FILE_EXTENSIONS_FOR_UPLOAD),
    },
    DOWNLOAD: {
        MAX_FOLDER_SIZE_BYTES: parseInt(process.env.REACT_APP_FOLDER_DOWNLOAD_MAX_SIZE, 10),
    }
};

export default config;