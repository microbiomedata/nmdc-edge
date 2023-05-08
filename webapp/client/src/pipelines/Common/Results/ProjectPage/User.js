import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Col, Row, } from 'reactstrap';
import ProjectSummary from '../ProjectSummary';
import ProjectResult from '../../../ProjectResult';
import { LoaderDialog } from "../../../../common/Dialogs";
import { postData } from '../../../../common/util';

const queryString = require('query-string');

function User(props) {
    const [code, setCode] = useState();
    const [project, setProject] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState();

    const user = useSelector(state => state.user);

    //componentDidMount()
    useEffect(() => {
        const parsed = queryString.parse(props.location.search);
        if (parsed.code) {
            setCode(parsed.code);
        } else {
            props.history.push("/user/projectlist");
        }
    }, [user, props]);

    useEffect(() => {
        function getProjectInfo() {
            let url = "/auth-api/user/project/info";
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
                                The project might be deleted or you have no permission to acces it.
                                <br></br>
                                {error}
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <>
                    <ProjectSummary project={project} />
                    <br></br>
                    <ProjectResult project={project} type={'user'} />
                </>
            }
        </div>
    );
}

export default User;