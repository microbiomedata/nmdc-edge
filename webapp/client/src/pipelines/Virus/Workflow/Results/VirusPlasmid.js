import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { JsonTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function VirusPlasmid(props) {
    const [activeTab, setActiveTab] = useState(0);
    const [collapseCard, setCollapseCard] = useState(true);

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
                        <NavItem key={"virusPlasmid0"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 0} onClick={() => { toggleTab(0); }} >
                                Virus prediction summary
                            </NavLink>
                        </NavItem>
                        <NavItem key={"virusPlasmid1"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 1} onClick={() => { toggleTab(1); }} >
                                Plasmid prediction summary
                            </NavLink>
                        </NavItem>
                        <NavItem key={"virusPlasmid2"}>
                            <NavLink style={{ cursor: 'pointer' }} active={activeTab === 2} onClick={() => { toggleTab(2); }} >
                                Virus quality summary
                            </NavLink>
                        </NavItem>
                    </Nav>
                    <TabContent activeTab={activeTab}>
                        <TabPane key={0} tabId={0}>
                            <br></br>
                            {props.result.virus_summary[0] ?
                                <JsonTable data={props.result.virus_summary} headers={Object.keys(props.result.virus_summary[0])} />
                                : <span>Empty table
                                    <br></br>
                                    <br></br></span>
                            }
                        </TabPane>
                        <TabPane key={1} tabId={1}>
                            <br></br>
                            {props.result.plasmid_summary[0] ?
                                <JsonTable data={props.result.plasmid_summary} headers={Object.keys(props.result.plasmid_summary[0])} />
                                : <span>Empty table
                                    <br></br>
                                    <br></br></span>
                            }
                        </TabPane>
                        <TabPane key={2} tabId={2}>
                            <br></br>
                            {props.result.quality_summary[0] ?
                                <JsonTable data={props.result.quality_summary} headers={Object.keys(props.result.quality_summary[0])} />
                                : <span>Empty table
                                    <br></br>
                                    <br></br></span>
                            }
                        </TabPane>
                    </TabContent>
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default VirusPlasmid;
