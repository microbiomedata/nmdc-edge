import React, { useState } from 'react';
import {
    Card, CardBody, Collapse,
} from 'reactstrap';

import { MyTooltip } from '../../../../common/MyTooltip';
import { FastqInput } from '../../../Common/Forms/FastqInput';
import { Header } from '../../../Common/Forms/CardHeader';
import { workflowInputTips } from '../Defaults';

export function ReadsQC(props) {
    const [collapseParms, setCollapseParms] = useState(true);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                <CardBody>
                    <MyTooltip id='ReadsQC' text="Input Raw Reads" tooltip={workflowInputTips['ReadsQC']['fastq_tip']} showTooltip={true} place="right" />
                    <FastqInput name={props.name} full_name={props.full_name} setParams={props.setParams} collapseParms={true} 
                    dataSources={['upload', 'project', 'public', 'globus']} projectTypes={['sra2fastq']} />
                </CardBody>
            </Collapse>
        </Card>
    );
}
