import React, { useState, useEffect } from 'react';
import ProjectSummary from '../ProjectSummary';
import ProjectResult from '../../../ProjectResult';
import { Col, Row } from 'reactstrap';
import { postData } from '../../../../common/util';

import { LoaderDialog } from "../../../../common/Dialogs";

const queryString = require('query-string');

function Public(props) {
    const [code, setCode] = useState();
    const [project, setProject] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState();

    useEffect(() => {
        const parsed = queryString.parse(props.location.search);
        if (parsed.code) {
            setCode(parsed.code);
        } else {
            props.history.push("/public/projectlist");
        }
    }, [props]);

    useEffect(() => {
        function getProjectInfo() {
            let url = "/api/project/info";
            const projData = {
                code: code
            };
            postData(url, projData)
                .then(data => {
                    setProject(data);
                    setLoading(false)
                })
                .catch(err => {
                    setError(err)
                    setLoading(false)
                });
        }
        if (code) {
            setLoading(true);
            getProjectInfo();
        }
    }, [code]);

    return (
        <div className="animated fadeIn">
            <LoaderDialog loading={loading} text="Loading..." />
            {error ?
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">Project not found</h4>
                            <hr />
                            <p className="text-muted float-left">
                                The project might be deleted or you have no permission to acces it.
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <>
                    <ProjectSummary project={project} />
                    <br></br>
                    <ProjectResult project={project} type={'public'} />
                </>
            }
        </div>
    );
}

export default Public;