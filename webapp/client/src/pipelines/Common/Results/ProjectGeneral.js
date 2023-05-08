import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import ReactJson from 'react-json-view'
import { JsonTable } from '../../../common/Tables';
import { Header } from './CardHeader';

function ProjectGeneral(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const [runStats, setRunStats] = useState([]);
    const [runStatsHeaders, setRunStatsHeaders] = useState([]);
    const [inputDisplay, setInputDisplay] = useState();

    const toggleCard = () => {
        setCollapseCard(!collapseCard);
    }

    useEffect(() => {
        if (props.stats && props.stats.stats && props.stats.stats.length > 0) {
            setRunStats(props.stats.stats);
            setRunStatsHeaders(Object.keys(props.stats.stats[0]));
        }
    }, [props.stats]);

    useEffect(() => {
        if (props.conf && props.conf.inputDisplay) {
            setInputDisplay(props.conf.inputDisplay);
        }
    }, [props.conf]);

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
                    {runStats.length > 0 &&
                        <JsonTable data={runStats} headers={runStatsHeaders} />
                    }
                    {inputDisplay &&
                    <>
                        <ReactJson src={inputDisplay} name={'Project Configuration'} enableClipboard={false} displayDataTypes={false} 
                        displayObjectSize={false} collapsed={true} />
                        <br></br>
                        </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default ProjectGeneral;
