import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse, Button } from 'reactstrap';
import ReactJson from 'react-json-view'
import { Header } from './CardHeader';
import { openLink } from '../../../common/util';

function Metadata(props) {
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
          {props.data &&
            <>
              <div className="edge-right">
                <Button
                  color="primary"
                  size="sm"
                  className="rounded-pill"
                  onClick={e => openLink(props.metadataSubmissionUrl)}
                  outline
                >
                 Update Metadata
                </Button>
                {/* <Button outline type="button" 
                  className="rounded-pill" size="sm" color="danger" onClick={e => props.setOpenMetadataDeletion(true)} >
                  Delete Metadata Submission
                </Button> */}
              </div>
              <br></br>
              <ReactJson src={props.data} name={'NMDC Submission Portal'} enableClipboard={false} displayDataTypes={false}
                displayObjectSize={false} collapsed={2} />
              <br></br>
            </>
          }
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default Metadata;