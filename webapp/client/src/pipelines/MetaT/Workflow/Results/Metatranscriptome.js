import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { Header } from '../../../Common/Results/CardHeader';
import Features from './Features';
import config from "../../../../config";

function Metatranscriptome(props) {
    const [collapseCard, setCollapseCard] = useState(true);
    const url = config.API.BASE_URI + "/projects/" + props.project.code + "/";

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
                    {props.result.features_tsv &&
                        <>
                            <a href={url + props.result.features_tsv} target="_blank" rel="noreferrer" >[ Export features as TSV ]</a>
                            <br></br><br></br>
                        </>
                    }
                    {props.result.features_json &&
                        <>
                            <h4 className="pt-3">Features</h4>
                            <Features result={props.result} />
                        </>
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default Metatranscriptome;
