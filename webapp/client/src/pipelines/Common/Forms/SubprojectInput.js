import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Collapse,
} from 'reactstrap';

import { Project } from './Project';
import { FastqInput } from './FastqInput';
import { Header } from './CardHeader';
import { MyTooltip } from '../../../common/MyTooltip';
import { initialSubprojectInput } from './Defaults';

export function SubprojectInput(props) {
    const [form, setState] = useState({ ...initialSubprojectInput });
    const [doValidation, setDoValidation] = useState(0);

    const [collapseParms, setCollapseParms] = useState(false);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const setProject = (params) => {
        setNewState2("project", params);
    }

    const setInput = (params) => {
        setNewState2("input", params);
    }
    
    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });
        setDoValidation(doValidation + 1);
    }

//trigger validation method when input changes
useEffect(() => {
    if (form.project && form.project.validForm && form.input && form.input.validForm) {
        form.validForm = true;
        form.errMessage = '';
    } else {
        form.validForm = false;
        form.errMessage = "Input error.";
    }
    //force updating parent's inputParams
    props.setParams(form, props.index);
}, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps


    return (
        <>
            <Card className="workflow-card">
                <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
                <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                    <CardBody>
                        <Project setParams={setProject} title={'Subproject Name'} />
                        <br></br>
                        <MyTooltip id='Metagenome-input' text="Input Raw Reads" tooltip={"test"} showTooltip={true} place="right" />
                        <FastqInput name={props.name} full_name={props.full_name} setParams={setInput} collapseParms={true} dataSources={['upload', 'public', 'globus']} />
                    </CardBody>
                </Collapse>
            </Card>
        </>
    );
}
