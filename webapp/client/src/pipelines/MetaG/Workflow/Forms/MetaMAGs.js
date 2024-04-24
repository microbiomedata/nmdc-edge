import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import { validFile } from '../../../../common/util';
import FileSelector from '../../../../common/FileSelector';
import { MyTooltip } from '../../../../common/MyTooltip';

import { initialMetaMAGs, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';

export function MetaMAGs(props) {

    const [form, setState] = useState({ ...initialMetaMAGs });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const handleFileSelection = (filename, fieldname, index, key) => {
        if (!validFile(key, filename)) {
            setState({
                ...form,
                ['input_' + fieldname + '_validInput']: false
            });
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        setState({
            ...form,
            ['input_' + fieldname]: filename, ['input_' + fieldname + '_validInput']: true, ['input_' + fieldname + '_display']: key
        });
        setDoValidation(doValidation + 1);
    }

    const handleOptionalFileSelection = (filename, fieldname, index, key) => {
        if (key && !validFile(key, filename)) {
            setState({
                ...form,
                ['input_' + fieldname + '_validInput']: false
            });
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        setState({
            ...form,
            ['input_' + fieldname]: filename, ['input_' + fieldname + '_validInput']: true, ['input_' + fieldname + '_display']: key
        });
        setDoValidation(doValidation + 1);
    }

    //trigger validation method when input changes
    useEffect(() => {
        let errMessage = '';

        if (!form.input_contig_validInput) {
            errMessage += "Invalid contig input<br />";
        }
        if (!form.input_sam_validInput) {
            errMessage += "Invalid sam/bam input<br />";
        }
        if (!form.input_gff_validInput) {
            errMessage += "Invalid gff input<br />";
        }
        if (!form.input_map_validInput) {
            errMessage += "Invalid map input<br />";
        }

        if (errMessage !== '') {
            form.validForm = false;
        } else {
            //errors only contains deleted dynamic input hidden errors
            form.validForm = true;
        }
        form.errMessage = errMessage;
        //force updating parent's inputParams
        props.setParams(form, props.full_name);
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                <CardBody>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-contig' text="Input Contig File" tooltip={workflowInputTips['MetaMAGs']['contig_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.input_contig_validInput}
                                dataSources={['project', 'upload', 'public', 'globus']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['fasta', 'fa', 'faa', 'fasta.gz', 'fa.gz', 'fna', 'fna.gz']}
                                fieldname={'contig'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-sam' text="Input Sam/Bam File" tooltip={workflowInputTips['MetaMAGs']['sam_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.input_sam_validInput}
                                dataSources={['upload', 'public']}
                                fileTypes={['sam', 'bam']} fieldname={'sam'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-gff' text="Input GFF File" tooltip={workflowInputTips['MetaMAGs']['gff_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.input_gff_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['gff']} fieldname={'gff'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-map' text="Input Map File" tooltip={workflowInputTips['MetaMAGs']['map_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleOptionalFileSelection}
                                enableInput={true}
                                placeholder={'(Optional) Select a file or enter a file http(s) url'}
                                validFile={form.input_map_validInput}
                                dataSources={['upload', 'public']}
                                fileTypes={['txt']} fieldname={'map'} viewFile={false}
                                isOptional={true} cleanupInput={true} />
                        </Col>
                    </Row>
                </CardBody>
            </Collapse>
        </Card>
    );
}
