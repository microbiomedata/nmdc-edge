import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { JsonTable } from '../../../common/Tables';
import { Header } from './CardHeader';

function RunStats(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const [runStats, setRunStats] = useState([]);
    const [runStatsHeaders, setRunStatsHeaders] = useState([]);

    const toggleCard = () => {
        setCollapseCard(!collapseCard);
    }

    useEffect(() => {
        if (props.stats.length > 0) {
            setRunStats(props.stats);
            setRunStatsHeaders(Object.keys(props.stats[0]));
        }
    }, [props.stats]);

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
                    <JsonTable data={runStats} headers={runStatsHeaders} />
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default RunStats;
