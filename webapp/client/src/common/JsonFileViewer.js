import React, { useEffect, useState } from 'react';
import ReactJson from 'react-json-view'
import { fetchFile } from './util';

function JsonFileViewer(props) {
    const [fileSrc, setFileSrc] = useState();
    useEffect(() => {
        fetchFile(props.url)
            .then(data => {
                setFileSrc(data);

            })
            .catch((error) => {
                alert(error);
                setFileSrc();
            });
    }, [props.url]);

    return (
        <>
            <h4>{props.name}</h4>
            <ReactJson src={fileSrc} enableClipboard={false} displayDataTypes={false} />
        </>
    );
};

export default JsonFileViewer;