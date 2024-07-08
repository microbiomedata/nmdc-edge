import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { Header } from '../../../Common/Results/CardHeader';
import MapBackTable from './MapBackTable';
import FeaturesTable from './FeaturesTable';

function ReadMapping(props) {
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
          {/* {props.mapback && <>
            <MapBackTable data={props.mapback} />
            <br></br>
          </>} */}
          {props.features && <>
            <FeaturesTable data={props.features} />
            <br></br>
          </>}
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default ReadMapping;
