import React, { useState, useEffect } from 'react';
import { Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink, Button, ButtonGroup } from 'reactstrap';
import { JsonTable, ArrayTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';
import config from "../../../../config";

function ReadbasedAnalysis(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const [activeTab, setActiveTab] = useState(0);
    const [summaryStats, setSummaryStats] = useState([]);
    const [summaryHeaders, setSummaryHeaders] = useState([]);
    const [summaryOpen, setSummaryOpen] = useState(true);
    const [taxOpen, setTaxOpen] = useState(true);
    const [taxTopData, setTaxTopData] = useState({ species: [], genus: [], family: [] });
    const [taxTopLevel, setTaxTopLevel] = useState("species");
    const taxTopHeaders = ["Tool", "Level", "Top1", "Top2", "Top3", "Top4", "Top5", "Top6", "Top7", "Top8", "Top9", "Top10"];
    const [detailOpen, setDetailOpen] = useState(true);
    const [detailData, setDetailData] = useState({});
    const [detailLevel, setDetailLevel] = useState("species");
    const detailHeaders = ["Level", "Taxonomy", "Reads", "Abundance"];

    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

    useEffect(() => {
        let summary = props.result.summary;
        let mystats = [];
        let taxTops = { species: [], genus: [], family: [] };
        let taxDetails = {};

        Object.keys(summary).forEach((tool, index) => {
            //setup summary data
            let counts = {
                "Tool": tool,
                "Classified Reads": summary[tool]["classifiedReadCount"],
                "Species Reads": summary[tool]["speciesReadCount"],
                "Species": summary[tool]["speciesCount"]
            };
            mystats.push(counts);
            //setup tax top10 data
            let tax = [tool, 'species'];
            //console.log(summary[tool]["taxonomyTop10"])
            if (summary[tool]["taxonomyTop10"]["species"] && summary[tool]["taxonomyTop10"]["species"]["data"]) {
                summary[tool]["taxonomyTop10"]["species"]["data"].forEach(item => {
                    tax.push(item[0]);
                });
            }
            taxTops["species"].push(tax);

            tax = [tool, 'genus'];
            if (summary[tool]["taxonomyTop10"]["genus"] && summary[tool]["taxonomyTop10"]["genus"]["data"]) {
                summary[tool]["taxonomyTop10"]["genus"]["data"].forEach(item => {
                    tax.push(item[0]);
                });
            }
            taxTops["genus"].push(tax);

            tax = [tool, 'family'];
            if (summary[tool]["taxonomyTop10"]["family"] && summary[tool]["taxonomyTop10"]["family"]["data"]) {
                summary[tool]["taxonomyTop10"]["family"]["data"].forEach(item => {
                    tax.push(item[0]);
                });
            }
            taxTops["family"].push(tax);

            //setup detail data
            taxDetails[tool] = {};
            taxDetails[tool]["species"] = [];
            if (summary[tool]["taxonomyTop10"]["species"] && summary[tool]["taxonomyTop10"]["species"]["data"]) {
                summary[tool]["taxonomyTop10"]["species"]["data"].forEach(item => {
                    let details = [];
                    details.push("species");
                    details.push(...item);
                    taxDetails[tool]["species"].push(details);
                });
            }

            taxDetails[tool]["genus"] = [];
            if (summary[tool]["taxonomyTop10"]["genus"] && summary[tool]["taxonomyTop10"]["genus"]["data"]) {
                summary[tool]["taxonomyTop10"]["genus"]["data"].forEach(item => {
                    let details = [];
                    details.push("genus");
                    details.push(...item);
                    taxDetails[tool]["genus"].push(details);
                });
            }

            taxDetails[tool]["family"] = [];
            if (summary[tool]["taxonomyTop10"]["family"] && summary[tool]["taxonomyTop10"]["family"]["data"]) {
                summary[tool]["taxonomyTop10"]["family"]["data"].forEach(item => {
                    let details = [];
                    details.push("family");
                    details.push(...item);
                    taxDetails[tool]["family"].push(details);
                });
            }

        });
        //console.log(taxDetails)
        setSummaryStats(mystats);
        setSummaryHeaders(Object.keys(mystats[0]));
        setTaxTopData(taxTops);
        //console.log("top", mystats)
        setDetailData(taxDetails);
    }, [props]);

    const toggleCard = () => {
        setCollapseCard(!collapseCard);
    }

    const toggleTab = (tab) => {
        setActiveTab(tab);
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
                    <span className="edge-link-large" onClick={() => setSummaryOpen(!summaryOpen)}>Summary</span>
                    <br></br><br></br>
                    {summaryOpen && <>
                        <JsonTable data={summaryStats} headers={summaryHeaders} />
                        <br></br>
                    </>
                    }
                    <span className="edge-link-large" onClick={() => setTaxOpen(!taxOpen)}>Taxonomy Top 10</span>
                    <br></br><br></br>
                    {taxOpen && <>
                        <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                            <Button color="outline-primary" onClick={() => setTaxTopLevel("species")}
                                active={taxTopLevel === 'species'}>Species</Button>
                            <Button color="outline-primary" onClick={() => setTaxTopLevel("genus")}
                                active={taxTopLevel === 'genus'}>Genus</Button>
                            <Button color="outline-primary" onClick={() => setTaxTopLevel("family")}
                                active={taxTopLevel === 'family'}>Family</Button>
                        </ButtonGroup>
                        <br></br><br></br>
                        <ArrayTable data={taxTopData[taxTopLevel]} headers={taxTopHeaders} />
                        <br></br>
                    </>
                    }
                    <span className="edge-link-large" onClick={() => setDetailOpen(!detailOpen)}>Detail</span>
                    <br></br><br></br>
                    {detailOpen && <>
                        <Nav tabs>
                            {Object.keys(props.result['html']).map((tool, index) => (
                                <NavItem key={tool + index}>
                                    <NavLink style={{ cursor: 'pointer' }} active={activeTab === index} onClick={() => { toggleTab(index); }} >
                                        {tool}
                                    </NavLink>
                                </NavItem>
                            ))}
                        </Nav>
                        <TabContent activeTab={activeTab}>
                            {Object.keys(props.result['html']).map((tool, index) => (
                                <TabPane key={index} tabId={index}>
                                    <br></br>
                                    <ButtonGroup className="mr-3" aria-label="First group" size="sm">
                                        <Button color="outline-primary" onClick={() => setDetailLevel("species")}
                                            active={detailLevel === 'species'}>Species</Button>
                                        <Button color="outline-primary" onClick={() => setDetailLevel("genus")}
                                            active={detailLevel === 'genus'}>Genus</Button>
                                        <Button color="outline-primary" onClick={() => setDetailLevel("family")}
                                            active={detailLevel === 'family'}>Family</Button>
                                    </ButtonGroup>
                                    <br></br><br></br>
                                    {detailData[tool] && detailData[tool][detailLevel] && <>
                                        <ArrayTable data={detailData[tool][detailLevel]} headers={detailHeaders} />
                                        <br></br><br></br>
                                    </>
                                    }
                                    {props.result['html'][tool]['htmls'].map((html, id) => (
                                        <div key={id} >
                                            <iframe src={url + html} className='edge-iframe' title={id}/>
                                            <a href={url + html} target="_blank" rel="noreferrer" >[Krona full window view]</a>
                                        </div>
                                    ))}
                                </TabPane>
                            ))}
                        </TabContent>
                    </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default ReadbasedAnalysis;
