import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { JsonTable, StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function MetaMAGs(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const [summaryStats, setSummaryStats] = useState({});
    const [mags, setMags] = useState();
    const [headers, setHeaders] = useState();

    useEffect(() => {
        let stats = props.result.stats;

        Object.keys(stats).forEach((item, index) => {
            if (typeof stats[item] === 'object') {
                setMags(stats[item].filter(obj => obj.bin_quality !== "LQ").sort((a, b) => {
                    let retval = 0;
                    if (a.bin_quality > b.bin_quality)
                        retval = 1;
                    if (a.bin_quality < b.bin_quality)
                        retval = -1;
                    if (retval === 0)
                        retval = a.completeness < b.completeness ? 1 : -1;
                    return retval;
                }));
                if (stats[item][0]) {
                    setHeaders(Object.keys(stats[item][0]));
                }
                delete stats[item];
            }
        });
        setSummaryStats(stats);
    }, [props]);

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
                    <span className="edge-link-large" >Summary</span>
                    <br></br><br></br>
                    <StatsTable data={summaryStats} headers={["Name", "Status"]} />
                    {headers && mags &&
                        <>
                            <span className="edge-link-large" >MAGs</span>
                            <br></br><br></br>
                            <JsonTable data={mags} headers={headers} />
                        </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default MetaMAGs;
