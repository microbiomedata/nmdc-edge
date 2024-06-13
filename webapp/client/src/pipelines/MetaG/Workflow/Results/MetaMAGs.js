import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { JsonTable, StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';
import config from "../../../../config";

function MetaMAGs(props) {
    const [activeTab, setActiveTab] = useState(0);
    const [collapseCard, setCollapseCard] = useState(true);
    const [summaryStats, setSummaryStats] = useState({});
    const [mags, setMags] = useState();
    const [headers, setHeaders] = useState();
    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

    const toggleTab = (tab) => {
        setActiveTab(tab);
    }

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
                    <Nav tabs>
                        <NavItem key={"metaMAGs0"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 0} onClick={() => { toggleTab(0); }} >
                                Summary
                            </NavLink>
                        </NavItem>
                        {headers && mags &&
                            <NavItem key={"metaMAGs1"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 1} onClick={() => { toggleTab(1); }} >
                                    MAGs
                                </NavLink>
                            </NavItem>
                        }
                        {props.result.barplot &&
                            <NavItem key={"metaMAGs2"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 2} onClick={() => { toggleTab(2); }} >
                                    Bar Plot
                                </NavLink>
                            </NavItem>
                        }
                        {props.result.heatmap &&
                            <NavItem key={"metaMAGs3"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 3} onClick={() => { toggleTab(3); }} >
                                    Heatmap
                                </NavLink>
                            </NavItem>
                        }
                        {props.result.kronaplot &&
                            <NavItem key={"metaMAGs4"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 4} onClick={() => { toggleTab(4); }} >
                                    Krona Plot
                                </NavLink>
                            </NavItem>
                        }
                    </Nav>
                    <TabContent activeTab={activeTab}>
                        <TabPane key={0} tabId={0}>
                            <br></br>
                            <StatsTable data={summaryStats} headers={["Name", "Status"]} />
                        </TabPane>
                        {headers && mags &&
                            <TabPane key={1} tabId={1}>
                                <br></br>
                                <JsonTable data={mags} headers={headers} />
                            </TabPane>
                        }
                        {props.result.barplot &&
                            <TabPane key={2} tabId={2}>
                                <a href={url + props.result.barplot} target="_blank" rel="noreferrer" >[Bar plot full window view]</a>
                                <br></br>
                                <br></br>
                                <br></br>
                                <div key={"metaMAGs-barplot"} >
                                    <img src={url + props.result.barplot} width="100%" height="100%" alt='barplot' />
                                    <br></br>
                                </div>
                            </TabPane>
                        }
                        {props.result.heatmap &&
                            <TabPane key={3} tabId={3}>
                                <a href={url + props.result.heatmap} target="_blank" rel="noreferrer" >[Heatmap full window view]</a>
                                <br></br>
                                <br></br>
                                <br></br>
                                <div key={"metaMAGs-heatmap"} >
                                    <img src={url + props.result.heatmap} width="100%" height="100%" alt='heatmap' />
                                    <br></br>
                                </div>
                            </TabPane>
                        }
                        {props.result.kronaplot &&
                            <TabPane key={4} tabId={4}>
                                <a href={url + props.result.kronaplot} target="_blank" rel="noreferrer" >[Krona Plot full window view]</a>
                                <br></br>
                                <br></br>
                                <br></br>
                                <div key={"metaMAGs-kronaplot"} >
                                    <iframe src={url + props.result.kronaplot} className='edge-iframe' title={"Krona Plot"} />
                                </div>
                            </TabPane>
                        }
                    </TabContent>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default MetaMAGs;
