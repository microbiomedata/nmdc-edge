import React, { useEffect, useState } from 'react';
import { Card, CardBody, Collapse } from 'reactstrap';
import { JsonTable, StatsTable } from '../../../../common/Tables';
import { Header } from '../../../Common/Results/CardHeader';

function Annotation(props) {
  const [collapseCard, setCollapseCard] = useState(true);
  const [seqStatsData, setSeqStatsData] = useState([]);
  const [seqStatsHeaders, setSeqStatsHeaders] = useState([]);
  const [seqOpen, setSeqOpen] = useState(true);
  const [geneStatsData, setGeneStatsData] = useState([]);
  const [geneStatsHeaders, setGeneStatsHeaders] = useState([]);
  const [geneOpen, setGeneOpen] = useState(true);
  const [infoStats, setInfoStats] = useState({});
  const [infoOpen, setInfoOpen] = useState(true);

  useEffect(() => {
    const stats = props.result;

    setInfoStats(stats["General Quality Info"]);

    let seqStatsArray = [];
    const seqStats = stats["Processed Sequences Statistics"];
    Object.keys(seqStats).forEach((type, index) => {
      let data = seqStats[type];
      data = { 'Data type': type, ...data };
      seqStatsArray.push(data);
    });

    setSeqStatsData(seqStatsArray);
    setSeqStatsHeaders(Object.keys(seqStatsArray[0]));

    let geneStatsArray = [];
    const geneStats = stats["Predicted Genes Statistics"];
    Object.keys(geneStats).forEach((feature, index) => {
      let array = geneStats[feature];
      let i = 0;
      for (i = 0; i < array.length; i++) {
        let mystats = array[i];
        let method = Object.keys(mystats)[0];
        let data = mystats[method];
        data = { 'Feature type': feature, 'Prediction method': method, ...data };
        geneStatsArray.push(data);
      }
    });

    setGeneStatsData(geneStatsArray);
    setGeneStatsHeaders(Object.keys(geneStatsArray[0]));

  }, [props.result]);

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
          <br></br>
          <span className="edge-link-large" onClick={() => setSeqOpen(!seqOpen)}>Processed Sequences Statistics</span>
          <br></br><br></br>
          {seqOpen && <>
            <JsonTable data={seqStatsData} headers={seqStatsHeaders} />
            <br></br>
          </>
          }
          <span className="edge-link-large" onClick={() => setGeneOpen(!geneOpen)}>Predicted Genes Statistics</span>
          <br></br><br></br>
          {geneOpen && <>
            <JsonTable data={geneStatsData} headers={geneStatsHeaders} />
            <br></br>
          </>
          }
          <span className="edge-link-large" onClick={() => setInfoOpen(!infoOpen)}>General Quality Info</span>
          <br></br><br></br>
          {infoOpen && <>
            <StatsTable data={infoStats} headers={["Name", "Status"]} />
            <br></br>
          </>
          }
        </CardBody>
      </Collapse>
    </Card>

  );
}

export default Annotation;
