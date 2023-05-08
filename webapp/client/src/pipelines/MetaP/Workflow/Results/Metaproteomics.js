import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { JsonTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function Metaproteomics(props) {
    const [collapseCard, setCollapseCard] = useState(true);

    const toggleCard = () => {
        setCollapseCard(!collapseCard);
    }

    useEffect(() => {
        if (props.allExpand > 0) {
            setCollapseCard(false);
        }
    }, [props.allExpand]);

    useEffect(() => {
        if (props.allClosed > 0) {
            setCollapseCard(true);
        }
    }, [props.allClosed]);

    return (

        <Card className='workflow-result-card'>
            <Header toggle={true} toggleParms={toggleCard} title={props.title} collapseParms={collapseCard} />
            <Collapse isOpen={!collapseCard} >
                <CardBody>
                    <h4>QC Metrics</h4>
                    <br></br>
                    <JsonTable data={props.result.quality_summary} headers={Object.keys(props.result.quality_summary[0])} />
                    <br></br>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default Metaproteomics;
