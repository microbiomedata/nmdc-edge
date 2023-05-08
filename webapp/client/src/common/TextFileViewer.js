import React, { useEffect, useState } from 'react';
import { fetchFile } from './util';

function TextFileViewer(props) {
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
            <div className="edge-display-linebreak ">
                {fileSrc}
            </div>
        </>
    );
};

export default TextFileViewer;