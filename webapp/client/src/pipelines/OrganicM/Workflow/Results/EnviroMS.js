import React, { useEffect, useState } from 'react';
import Select from 'react-select';
import { Col, Row, Card, CardBody, Collapse } from 'reactstrap';
import ReactJson from 'react-json-view';
import { Header } from '../../../Common/Results/CardHeader';
import TopMolecules from './TopMolecules';
import config from "../../../../config";

function EnviroMS(props) {
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
                                <Col xs="12" md="2">
                                    <h4 className="pt-3">Input</h4>
                                </Col>
                                <Col xs="12" md="10">
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
                            <h4 className="pt-3">Metadata</h4>
                            <ReactJson src={props.result.stats[input]['conf']} name={'workflow metadata'} enableClipboard={false} displayDataTypes={false}
                                displayObjectSize={false} collapsed={true} />
                            <br></br>

                            {props.result.stats[input]['molecules_tsv'] &&
                                <>
                                    <h4 className="pt-3">Molecules</h4>
                                    <a href={url + props.result.stats[input]['molecules_tsv']} target="_blank" rel="noreferrer" >[ Export molecules as TSV ]</a>
                                    <br></br><br></br>
                                </>
                            }
                            {props.result.stats[input]['molecules_json'] &&
                                <>
                                    <h4 className="pt-3">Molecules</h4>
                                    <TopMolecules result={props.result.stats[input]} />
                                </>
                            }
                        </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default EnviroMS;
