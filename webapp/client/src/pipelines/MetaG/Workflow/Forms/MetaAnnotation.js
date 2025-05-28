import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import { validFile } from '../../../../common/util';
import FileSelector from '../../../../common/FileSelector';

import { useForm } from "react-hook-form";
import { defaults, initialMetaAnnotation, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';
import { MyTooltip } from '../../../../common/MyTooltip';

export function MetaAnnotation(props) {
    const { register, setValue, formState: { errors }, trigger } = useForm({
        mode: defaults['form_mode'],
    });

    const [form, setState] = useState({ ...initialMetaAnnotation });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const handleFastaFileSelection = (filename, type, index, key) => {
        if (!validFile(key, filename)) {

            setState({
                ...form,
                ['input_fasta_validInput']: false
            });
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }

        setState({
            ...form,
            ['input_fasta']: filename, ['input_fasta_validInput']: true, ['input_fasta_display']: key
        });
        setValue("fasta_hidden", filename, { shouldValidate: true });
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

                if (errors.fasta_hidden) {
                    errMessage += errors.fasta_hidden.message + "<br />";
                }
                if (errMessage !== '') {
                    errMessage = "<br /><div class='edge-form-input-error'>Metagenome Annotation</div>" + errMessage;
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
                            <MyTooltip id='MetaAnnotation' text="Input FASTA File" tooltip={workflowInputTips['MetaAnnotation']['fasta_tip']} showTooltip={true} place="right" /></Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFastaFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.input_fasta_validInput}
                                dataSources={['project', 'upload', 'public', 'globus']}
                                fileTypes={['fasta', 'fa', 'fna', 'fasta.gz', 'fa.gz', 'fna.gz']}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Assembly']} viewFile={false} />

                            <input type="hidden" name="fasta_hidden" id="fasta_hidden"
                                value={form['input_fasta']}
                                {...register("fasta_hidden", { required: 'Fasta file is required' })} />
                        </Col>
                    </Row>
                </CardBody>
            </Collapse>
        </Card>
    );
}
