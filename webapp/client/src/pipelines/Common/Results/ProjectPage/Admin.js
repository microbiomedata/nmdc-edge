import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Col, Row, } from 'reactstrap';
import queryString from 'query-string';
import ProjectSummary from '../ProjectSummary';
import ProjectResult from '../../../ProjectResult';

import { LoaderDialog } from "../../../../common/Dialogs";
import { postData } from '../../../../common/util';

function Admin(props) {
    const [code, setCode] = useState();
    const [project, setProject] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState();
    const user = useSelector(state => state.user);

    //componentDidMount()
    useEffect(() => {
        if (user.profile.type !== "admin") {
            props.history.push("/home");
        } else {
            const parsed = queryString.parse(props.location.search);
            if (parsed.code) {
                setCode(parsed.code);
            } else {
                props.history.push("/admin/projectlist");
            }
        }
    }, [user, props]);

    useEffect(() => {
        function getProjectInfo() {
            let url = "/auth-api/admin/project/info";
            const projData = {
                code: code,
            };
            postData(url, projData)
                .then(data => {
                    setProject(data);
                    setLoading(false)
                })
                .catch(err => {
                    setError(err);
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
                                The project might be deleted or you have no permission to access it.
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <>
                    <ProjectSummary project={project} type={'admin'} />
                    <br></br>
                    <ProjectResult project={project} type={'admin'} />
                </>
            }
        </div>
    );
}

export default Admin;