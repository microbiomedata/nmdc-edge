import React from 'react';
import ProjectTable from '../../../common/UM/Common/ProjectTable';

function BulkSubmissionProjects(props) {

  return (
    <>
      <ProjectTable tableType={props.tableType} bulkSubmissionCode={props.code} {...props} />
    </>
  );
}

export default BulkSubmissionProjects;
