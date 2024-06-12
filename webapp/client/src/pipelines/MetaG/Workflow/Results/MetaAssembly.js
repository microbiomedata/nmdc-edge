import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';
import config from "../../../../config";

function MetaAssembly(props) {
    const [activeTab, setActiveTab] = useState(0);
    const [collapseCard, setCollapseCard] = useState(true);
    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

    const toggleTab = (tab) => {
        setActiveTab(tab);
    }

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
                        <NavItem key={"metaAssembly0"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 0} onClick={() => { toggleTab(0); }} >
                                Status
                            </NavLink>
                        </NavItem>
                        {props.result.reportHtml &&
                            <NavItem key={"metaAssembly1"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 1} onClick={() => { toggleTab(1); }} >
                                    Report
                                </NavLink>
                            </NavItem>
                        }
                    </Nav>
                    <TabContent activeTab={activeTab}>
                        <TabPane key={0} tabId={0}>
                            <br></br>
                            <StatsTable data={props.result.stats} headers={["Name", "Status"]} />
                        </TabPane>
                        {props.result.reportHtml &&
                            <TabPane key={1} tabId={1}>
                                <a href={url + props.result.reportHtml} target="_blank" rel="noreferrer" >[Report full window view]</a>
                                <br></br>
                                <div key={"metaAssembly-report"} >
                                    <iframe src={url + props.result.reportHtml} className='edge-iframe' title={"Workflow Report"} />
                                </div>
                            </TabPane>
                        }
                    </TabContent>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default MetaAssembly;
