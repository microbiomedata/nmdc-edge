import React from 'react';
import BulkSubmission from '../../BulkSubmission/Forms/BulkSubmission';
import { workflowOptions } from './Defaults';

function Main(props) {
    return (
      <BulkSubmission workflowOptions={workflowOptions} category={"Metaproteomics"} {...props}/>
    );
}

export default Main;