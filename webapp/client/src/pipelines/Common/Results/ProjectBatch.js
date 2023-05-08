import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { Header } from './CardHeader';

import ProjectTable from '../../../common/UM/Common/ProjectTable';

import PublicProjectTable from '../../../common/UM/Public/ProjectTable';

function ProjectGeneral(props) {
    const [collapseCard, setCollapseCard] = useState(true);

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
                    {props.userType === 'public' ?
                        <PublicProjectTable projectType={'batch'} tableNoRecordsMsg={'Projects might be deleted'} code={props.project.code} />
                        :
                        <ProjectTable reloadOutputs={props.reloadOutputs} tableType={props.userType} code={props.project.code} projectType={'batch'} tableNoRecordsMsg={'Projects might be deleted'} tableSelection={true}  />
                    }
                </CardBody>
            </Collapse>
        </Card>

    );
}

export default ProjectGeneral;
