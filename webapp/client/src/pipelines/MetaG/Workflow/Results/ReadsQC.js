import React, { useEffect, useState } from 'react';
import Select from 'react-select';
import { Col, Row, Card, CardBody, Collapse, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';
import config from "../../../../config";

function ReadsQC(props) {
    const [activeTab, setActiveTab] = useState(0);
    const [collapseCard, setCollapseCard] = useState(true);
    const [input, setInput] = useState();
    const [inputOptions, setInputOptions] = useState();
    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

    useEffect(() => {
        let options = Object.keys(props.result.stats).map(item => {
            return { value: item, label: item };
        });
        setInputOptions(options);
        setInput(options[0].value);
    }, [props.result.stats]);

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
                    {(props.result.reportHtml && props.result.summaries) ? <>
                        <Nav tabs>
                            <NavItem key={"readsQC0"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 0} onClick={() => { toggleTab(0); }} >
                                    Report
                                </NavLink>
                            </NavItem>

                            <NavItem key={"readsQC1"}>
                                <NavLink style={{ cursor: 'pointer' }} active={activeTab === 1} onClick={() => { toggleTab(1); }} >
                                    Summary
                                </NavLink>
                            </NavItem>
                        </Nav>
                        <TabContent activeTab={activeTab} >
                            <TabPane key={0} tabId={0}>
                                <a href={url + props.result.reportHtml} target="_blank" rel="noreferrer" >[Report full window view]</a>
                                <br></br><br></br>
                                <div key={"readsQC-report"} >
                                    <embed src={url + props.result.reportHtml} className='edge-iframe' title={"multiqc_report"} />
                                </div>

                            </TabPane>
                            <TabPane key={1} tabId={1}>
                                {inputOptions && <>
                                    <a href={url + props.result.summaries[input]} target="_blank" rel="noreferrer" >[Summary full window view]</a>
                                    <br></br>
                                    <br></br>
                                    <Row>
                                        <Col xs="12" md="1">
                                            Input
                                        </Col>
                                        <Col xs="12" md="11">
                                            <Select
                                                defaultValue={inputOptions[0]}
                                                options={inputOptions}
                                                onChange={e => {
                                                    if (e) {
                                                        setInput(e.value);
                                                    } else {
                                                    }
                                                }}
                                            />
                                        </Col>
                                    </Row>
                                    <div key={"readsQC-summary"} >
                                        <embed src={url + props.result.summaries[input]} className='edge-iframe' title={"qc summary"} />
                                    </div>
                                </>
                                }
                            </TabPane>
                        </TabContent>
                    </> :
                        <>
                            {inputOptions && <>
                                <Row>
                                    <Col xs="12" md="1">
                                        Input
                                    </Col>
                                    <Col xs="12" md="11">
                                        <Select
                                            defaultValue={inputOptions[0]}
                                            options={inputOptions}
                                            onChange={e => {
                                                if (e) {
                                                    setInput(e.value);
                                                } else {
                                                }
                                            }}
                                        />
                                    </Col>
                                </Row>
                                <br></br>
                                <StatsTable data={props.result.stats[input]} headers={["Reads", "Status"]} />
                            </>
                            }
                        </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default ReadsQC;
