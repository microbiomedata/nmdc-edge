import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function ReadsQC(props) {
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
          <StatsTable data={props.result} headers={["Reads", "Status"]} />
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default ReadsQC;
