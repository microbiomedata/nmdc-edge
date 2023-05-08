import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import FileSelector from '../../../../common/FileSelector';
import { MyTooltip } from '../../../../common/MyTooltip';

import { useForm } from "react-hook-form";
import { defaults, initialMetaMAGs, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';

export function MetaMAGs(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });

    const [form, setState] = useState({...initialMetaMAGs});
    const [collapseParms, setCollapseParms] = useState(true);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const handleFileSelection = (filename, fieldname, index, key) => {
        setState({
            ...form,
            ['input_' + fieldname]: filename, ['input_' + fieldname + '_display']: key
        });
        setValue(fieldname + "_hidden", filename, { shouldValidate: true });
        setDoValidation(doValidation + 1);
    }

    //trigger validation method when input changes
    useEffect(() => {
        //validate form
        trigger().then(result => {
            form.validForm = result;
            if (result) {
                form.errMessage = '';
            } else {
                let errMessage = '';

                if (errors.contig_hidden) {
                    errMessage += errors.contig_hidden.message + "<br />";
                }
                if (errors.bam_hidden) {
                    errMessage += errors.bam_hidden.message + "<br />";
                }
                if (errors.gff_hidden) {
                    errMessage += errors.gff_hidden.message + "<br />";
                }
                if (errMessage !== '') {
                    errMessage = "<br /><div class='edge-form-input-error'>Metagenome MAGs</div>" + errMessage;
                } else {
                    //errors only contains deleted dynamic input hidden errors
                    form.validForm = true;
                }
                form.errMessage = errMessage;
            }
            //force updating parent's inputParams
            props.setParams(form, props.full_name);
        });
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
                            <FileSelector onChange={handleFileSelection} dataSources={['project', 'upload', 'public', 'globus']}
                                projectTypes={['Metagenome Annotation']} 
                                fileTypes={['fasta', 'fa','faa', 'fasta.gz', 'fa.gz', 'fna', 'fna.gz']} fieldname={'contig'} viewFile={false} />

                            <input type="hidden" name="contig_hidden" id="contig_hidden"
                                value={form['input_contig']}
                                {...register("contig_hidden", { required: 'Contig file is required' })} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-sam' text="Input Sam/Bam File" tooltip={workflowInputTips['MetaMAGs']['sam_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection} dataSources={['upload', 'public']}
                                fileTypes={['sam', 'bam']} fieldname={'sam'} viewFile={false} />

                            <input type="hidden" name="sam_hidden" id="sam_hidden"
                                value={form['input_sam']}
                                {...register("sam_hidden", { required: 'Sam file is required' })} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-gff' text="Input GFF File" tooltip={workflowInputTips['MetaMAGs']['gff_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection} dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']} 
                                fileTypes={['gff']} fieldname={'gff'} viewFile={false} />

                            <input type="hidden" name="gff_hidden" id="gff_hidden"
                                value={form['input_gff']}
                                {...register("gff_hidden", { required: 'GFF file is required' })} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-map' text="Input Map File" tooltip={workflowInputTips['MetaMAGs']['map_tip']} showTooltip={true} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection} dataSources={['upload', 'public']}
                                fileTypes={['txt']} fieldname={'map'} viewFile={false} placeholder={'Optional'}
                                isOptional={true} cleanupInput={true} />
                        </Col>
                    </Row>
                </CardBody>
            </Collapse>
        </Card>
    );
}
