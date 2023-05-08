import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { JsonTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function VirusPlasmid(props) {
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
                    <h4>Virus prediction summary</h4>
                    <br></br>
                    {props.result.virus_summary[0] ?
                        <JsonTable data={props.result.virus_summary} headers={Object.keys(props.result.virus_summary[0])} />
                        : <span>Empty table
                            <br></br>
                            <br></br></span>
                    }
                    <br></br>
                    <h4>Plasmid prediction summary</h4>
                    <br></br>
                    {props.result.plasmid_summary[0] ?
                        <JsonTable data={props.result.plasmid_summary} headers={Object.keys(props.result.plasmid_summary[0])} />
                        : <span>Empty table
                            <br></br>
                            <br></br></span>
                    }
                    <br></br>
                    <h4>Virus quality summary</h4>
                    <br></br>
                    {props.result.quality_summary[0] ?
                        <JsonTable data={props.result.quality_summary} headers={Object.keys(props.result.quality_summary[0])} />
                        : <span>Empty table
                            <br></br>
                            <br></br></span>
                    }
                    <br></br>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default VirusPlasmid;
