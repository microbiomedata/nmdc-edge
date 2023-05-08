import React, { useEffect } from 'react';
import jwt_decode from "jwt-decode";

const queryString = require('query-string');

function ORCIDOAuthCallback(props) {

    useEffect(() => {
        const parsed = queryString.parse(props.location.hash);
        //console.log("parsed", parsed.id_token)
        const decoded = jwt_decode(parsed.id_token);
        //console.log("decode", decoded);
        //pass user profile to SocialLogin
        window.opener.postMessage(decoded)
        window.close();
    }, [props]);


    return (
        <div className="animated fadeIn">
            hi ORCiD
        </div>
    );
}

export default ORCIDOAuthCallback;