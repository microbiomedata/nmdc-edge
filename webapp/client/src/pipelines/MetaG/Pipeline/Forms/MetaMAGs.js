import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import { MyTooltip } from '../../../../common/MyTooltip';
import FileSelector from '../../../../common/FileSelector';
import { Header } from '../../../Common/Forms/CardHeader';
import { initialMetaMAGs, workflowInputTips } from '../Defaults';

export function MetaMAGs(props) {

    const [form, setState] = useState({...initialMetaMAGs});
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);


    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });
        setDoValidation(doValidation + 1);
    }

    const toggleParms = () => {
        if (form.paramsOn) {
            setCollapseParms(!collapseParms);
        }
    }

    const handleFileSelection = (filename, fieldname, index, key) => {
        setState({
            ...form,
            ['input_' + fieldname]: filename, ['input_' + fieldname + '_display']: key
        });
        setDoValidation(doValidation + 1);
    }

    const setOnoff = (stats) => {
        if (props.onoff) {
            setNewState2("paramsOn", stats);
        }
    }

    useEffect(() => {
        if (!props.onoff) {
            setNewState2("paramsOn", false);
            setCollapseParms(true);
        }
    }, [props.onoff]);// eslint-disable-line react-hooks/exhaustive-deps

    //trigger validation method when click submit
    useEffect(() => {
        //force updating parent's inputParams
        props.setParams(form, props.name);
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Card className='workflow-card'>
            <Header toggle={true} toggleParms={toggleParms} title={props.full_name} collapseParms={collapseParms}
                onoff={true} setOnoff={setOnoff} setCollapseParms={setCollapseParms} paramsOn={form.paramsOn} />
            <Collapse isOpen={!collapseParms} id="collapseParameters">
                <CardBody>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='Metagenome-map' text="Input Map File" tooltip={workflowInputTips['MetaMAGs']['map_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection} dataSources={['project', 'upload', 'public']}
                                fileTypes={['txt', 'tsv']} fieldname={'map'} viewFile={false} placeholder={'Optional'}
                                isOptional={true} cleanupInput={true} />

                        </Col>
                    </Row>
                    <br></br>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='Metagenome-domain' text="Input Domain File" tooltip={workflowInputTips['MetaMAGs']['domain_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection} dataSources={['project', 'upload', 'public']}
                                fileTypes={['txt', 'tsv']} fieldname={'domain'} viewFile={false} placeholder={'Optional'}
                                isOptional={true} cleanupInput={true} />

                        </Col>
                    </Row>

                </CardBody>
            </Collapse>
        </Card>
    );
}


