import React, { useEffect, useState } from 'react';
import Select from 'react-select';
import { Col, Row, Card, CardBody, Collapse } from 'reactstrap';
import { StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function ReadsQC(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const [input, setInput] = useState();
    const [inputOptions, setInputOptions] = useState();
    useEffect(() => {
        let options = Object.keys(props.result.stats).map(item => {
            return { value: item, label: item };
        });
        setInputOptions(options);
        setInput(options[0].value);
    }, [props.result.stats]);

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
                    {inputOptions &&
                        <>
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
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default ReadsQC;
