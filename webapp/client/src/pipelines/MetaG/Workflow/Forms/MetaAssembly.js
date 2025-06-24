import React, { useState } from 'react';
import {
    Card, CardBody, Collapse,
} from 'reactstrap';

import { FastqInput } from '../../../Common/Forms/FastqInput';
import { Header } from '../../../Common/Forms/CardHeader';
import { MyTooltip } from '../../../../common/MyTooltip';
import { workflowInputTips } from '../Defaults';

export function MetaAssembly(props) {
    const [collapseParms, setCollapseParms] = useState(false);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                <CardBody>
                    <MyTooltip id='MetaAssembly' text="Input FASTQ File" tooltip={workflowInputTips['MetaAssembly']['fastq_tip']} showTooltip={true} place="right" />
                    <FastqInput projectTypes={['Metagenome Pipeline','ReadsQC','Retrieve SRA Data']} name={props.name} full_name={props.full_name} 
                    setParams={props.setParams} collapseParms={true} platformOptions={true} />
                </CardBody>
            </Collapse>
        </Card>
    );
}
