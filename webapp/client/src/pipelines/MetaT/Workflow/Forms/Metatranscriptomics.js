import React, { useState } from 'react';
import {
    Card, CardBody, Collapse,
} from 'reactstrap';

import { FastqInput } from '../../../Common/Forms/FastqInput';
import { Header } from '../../../Common/Forms/CardHeader';
import { initialMetatranscriptomics, workflowInputTips } from '../Defaults';
import { MyTooltip } from '../../../../common/MyTooltip';

export function Metatranscriptomics(props) {
    const [collapseParms, setCollapseParms] = useState(false);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                <CardBody>
                    <MyTooltip id='Metatranscriptomics' text="Input Raw Reads" tooltip={workflowInputTips['Metatranscriptomics']['fastq_tip']} showTooltip={true} place="right" />
                    <FastqInput name={props.name} full_name={props.full_name} setParams={props.setParams} single-input-max={1} paired-input-max={1}
                    collapseParms={true} dataSources={['upload', 'project', 'public', 'globus']} projectTypes={['Retrieve SRA Data']} />
                </CardBody>
            </Collapse>
        </Card>
    );
}
