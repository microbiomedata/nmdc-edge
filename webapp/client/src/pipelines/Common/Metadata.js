import React, { useEffect, useState } from 'react';
import {
  Card, CardBody, Collapse,
} from 'reactstrap';

import { getData } from '../../common/util';
import MetadataInput from './Forms/MetadataInput';
import { Header } from './Forms/CardHeader';

export function Metadata(props) {
  const [connect2nmdcserver, setConnect2nmdcserver] = useState(false);
  const [collapseParms, setCollapseParms] = useState(false);

  const toggleParms = () => {
    setCollapseParms(!collapseParms);
  }

  useEffect(() => {
    let url = "/auth-api/user/project/connect2nmdcserver";
    getData(url)
      .then(data => {
        //console.log(data)
        setConnect2nmdcserver(data.connect2nmdcserver);
      })
      .catch(error => {
        alert(error);
      });
  }, []);

  return (
    <>
      {!connect2nmdcserver &&
        <>
          <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={props.title} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
              <CardBody>
                <MetadataInput name={props.name} full_name={props.full_name} setParams={props.setParams} collapseParms={true} />
              </CardBody>
            </Collapse>
          </Card>
        </>
      }
    </>
  );
}
