import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { JsonTable, StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';
import config from "../../../../config";

function MetaAnnotation(props) {
    const [activeTab, setActiveTab] = useState(0);
    const [collapseCard, setCollapseCard] = useState(true);
    const [seqStatsData, setSeqStatsData] = useState([]);
    const [seqStatsHeaders, setSeqStatsHeaders] = useState([]);
    const [seqOpen, setSeqOpen] = useState(true);
    const [geneStatsData, setGeneStatsData] = useState([]);
    const [geneStatsHeaders, setGeneStatsHeaders] = useState([]);
    const [geneOpen, setGeneOpen] = useState(true);
    const [infoStats, setInfoStats] = useState({});
    const [infoOpen, setInfoOpen] = useState(true);
    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

    const toggleTab = (tab) => {
        setActiveTab(tab);
    }

    useEffect(() => {
        const stats = props.result.stats;

        setInfoStats(stats["General Quality Info"]);

        let seqStatsArray = [];
        const seqStats = stats["Processed Sequences Statistics"];
        Object.keys(seqStats).forEach((type, index) => {
            let data = seqStats[type];
            data = { 'Data type': type, ...data };
            seqStatsArray.push(data);
        });

        setSeqStatsData(seqStatsArray);
        setSeqStatsHeaders(Object.keys(seqStatsArray[0]));

        let geneStatsArray = [];
        const geneStats = stats["Predicted Genes Statistics"];
        Object.keys(geneStats).forEach((feature, index) => {
            let array = geneStats[feature];
            let i = 0;
            for (i = 0; i < array.length; i++) {
                let mystats = array[i];
                let method = Object.keys(mystats)[0];
                let data = mystats[method];
                data = { 'Feature type': feature, 'Prediction method': method, ...data };
                geneStatsArray.push(data);
            }
        });

        setGeneStatsData(geneStatsArray);
        setGeneStatsHeaders(Object.keys(geneStatsArray[0]));

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
                        <NavItem key={"metaAnnotation0"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 0} onClick={() => { toggleTab(0); }} >
                                Statistics
                            </NavLink>
                        </NavItem>
                        {props.result.proteinSizeHistogram &&
                            <NavItem key={"metaAnnotation1"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 1} onClick={() => { toggleTab(1); }} >
                                    Protein Size Histogram
                                </NavLink>
                            </NavItem>
                        }
                        {props.result.opaverWebPath &&
                            <NavItem key={"metaAnnotation2"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 2} onClick={() => { toggleTab(2); }} >
                                    Opaver Web Path
                                </NavLink>
                            </NavItem>
                        }
                    </Nav>
                    <TabContent activeTab={activeTab}>
                        <TabPane key={0} tabId={0}>
                            <br></br>
                            <span className="edge-link-large" onClick={() => setSeqOpen(!seqOpen)}>Processed Sequences Statistics</span>
                            <br></br><br></br>
                            {seqOpen && <>
                                <JsonTable data={seqStatsData} headers={seqStatsHeaders} />
                                <br></br>
                            </>
                            }
                            <span className="edge-link-large" onClick={() => setGeneOpen(!geneOpen)}>Predicted Genes Statistics</span>
                            <br></br><br></br>
                            {geneOpen && <>
                                <JsonTable data={geneStatsData} headers={geneStatsHeaders} />
                                <br></br>
                            </>
                            }
                            <span className="edge-link-large" onClick={() => setInfoOpen(!infoOpen)}>General Quality Info</span>
                            <br></br><br></br>
                            {infoOpen && <>
                                <StatsTable data={infoStats} headers={["Name", "Status"]} />
                                <br></br>
                            </>
                            }
                        </TabPane>
                        {props.result.proteinSizeHistogram &&
                            <TabPane key={1} tabId={1}>
                                <a href={url + props.result.proteinSizeHistogram} target="_blank" rel="noreferrer" >[Histogram full window view]</a>
                                <br></br>
                                <div key={"metaAnnotation-proteinSizeHistogram"} >
                                    <iframe src={url + props.result.proteinSizeHistogram} className='edge-iframe' title={"Protein Size Histogram"} />
                                </div>
                            </TabPane>
                        }
                        {props.result.opaverWebPath &&
                            <TabPane key={2} tabId={2}>
                                <a href={config.API.BASE_URI + "/" + props.result.opaverWebPath} target="_blank" rel="noreferrer" >[Opaver full window view]</a>
                                <br></br>
                                <div key={"metaAnnotation-opaverWebPath"} >
                                    <iframe src={config.API.BASE_URI + "/" + props.result.opaverWebPath} className='edge-iframe' title={"Opaver Web Path"} />
                                </div>
                            </TabPane>
                        }
                    </TabContent>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default MetaAnnotation;
