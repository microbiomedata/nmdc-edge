import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Col, Row, } from 'reactstrap';
import queryString from 'query-string';
import BulkSubmissionSummary from '../BulkSubmissionSummary';
import BulkSubmissionResult from '../../../BulkSubmission/BulkSubmissionResult';
import { LoaderDialog } from "../../../../common/Dialogs";
import { postData } from '../../../../common/util';

function User(props) {
    const [code, setCode] = useState();
    const [bulkSubmission, setBulkSubmission] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState();

    const user = useSelector(state => state.user);

    //componentDidMount()
    useEffect(() => {
        const parsed = queryString.parse(props.location.search);
        if (parsed.code) {
            setCode(parsed.code);
        } else {
            props.history.push("/user/bulksubmissionlist");
        }
    }, [user, props]);

    useEffect(() => {
        function getBulkSubmissionInfo() {
            let url = "/auth-api/user/bulkSubmission/info";
            const projData = {
                code: code,
            };
            postData(url, projData)
                .then(data => {
                    setBulkSubmission(data);
                    setLoading(false)
                })
                .catch(err => {
                    setError(err);
                    setLoading(false)
                });
        }
        if (code) {
            setLoading(true);
            getBulkSubmissionInfo();
        }
    }, [code]);



    return (
        <div className="animated fadeIn">
            <LoaderDialog loading={loading} text="Loading..." />
            {error ?
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <h4 className="pt-3">BulkSubmission not found</h4>
                            <hr />
                            <p className="text-muted float-left">
                                The bulkSubmission might be deleted or you have no permission to access it.
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <>
                    <BulkSubmissionSummary bulkSubmission={bulkSubmission} type={'user'} />
                    <br></br>
                    <BulkSubmissionResult bulkSubmission={bulkSubmission} type={'user'} {...props} />
                </>
            }
        </div>
    );
}

export default User;