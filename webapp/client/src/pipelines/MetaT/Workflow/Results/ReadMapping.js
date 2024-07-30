import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { Header } from '../../../Common/Results/CardHeader';
import FeaturesTable from './FeaturesTable';
import config from "../../../../config";

function ReadMapping(props) {
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
          {props.tooLarge ?
            <>
              The result is too large to display.
              <br></br>
              <a href={url + props.features} target="_blank" rel="noreferrer" >[ Export the result as TSV ]</a>
              <br></br><br></br>
            </>
            : <>
              <FeaturesTable data={props.features} />
              <br></br>
            </>}
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default ReadMapping;
