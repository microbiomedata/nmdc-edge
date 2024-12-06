import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import ReactJson from 'react-json-view'
import { Header } from './CardHeader';

function BulkSubmissionGeneral(props) {
  const [collapseCard, setCollapseCard] = useState(true);
  const [inputDisplay, setInputDisplay] = useState();

  const toggleCard = () => {
    setCollapseCard(!collapseCard);
  }

  useEffect(() => {
    if (props.conf && props.conf.inputDisplay) {
      setInputDisplay(props.conf.inputDisplay);
    }
  }, [props.conf]);

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
          {inputDisplay &&
            <>
              <ReactJson src={inputDisplay} name={'Bulk Submission'} enableClipboard={false} displayDataTypes={false}
                displayObjectSize={false} collapsed={false} />
              <br></br>
            </>
          }
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default BulkSubmissionGeneral;
