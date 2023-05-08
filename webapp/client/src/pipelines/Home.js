import React from 'react';
import { Col, Row } from 'reactstrap';

function Home() {
  return (
    <div className="animated fadeIn">
      <Row className="justify-content-center">
        <Col xs="12" sm="12" md="12">
          <div className="clearfix">
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              The National Microbiome Data Collaborative (<a href='https://microbiomedata.org/' target='_blank' rel="noreferrer">NMDC</a>) is an effort to make microbiome
            data findable, accessible, interoperable, and reusable (FAIR) by providing search functions and access to standardized data and data products
            in an open and integrative data science system. <a href='https://edgebioinformatics.org/' target='_blank' rel="noreferrer">EDGE bioinformatics</a> is an
            open-source bioinformatics platform with a user-friendly interface that allows scientists to perform a number of bioinformatics analyses
            using state-of-the-art tools and algorithms. NMDC EDGE presents users with the ability to run NMDC workflows on raw omics data within an
            updated EDGE Bioinformatics framework.
            </p>
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              A <a href={process.env.REACT_APP_API_URL + "/docs/help/quickStart.pdf"} target="_blank" rel="noreferrer">Quick Start guide</a> is available for running the NMDC workflows
            in NMDC EDGE. See the <a href="https://nmdc-workflow-documentation.readthedocs.io/en/latest/chapters/overview.html" target="_blank" rel="noreferrer">full NMDC
            Workflows documentation</a> for more information, including required databases and resources needed for native installation. 
            The current release of NMDC EDGE contains metagenomic workflows only.
            Other NMDC workflows for metatranscriptomic, metaproteomic and metabolomic data analysis will be added to NMDC EDGE in future releases.
            </p>
            <br></br><br></br>
            <p className="edge-text-font edge-text-size-large float-left" style={{ fontStyle: 'italic' }}>
              This <b>beta version of the NMDC EDGE platform</b> is running in an HPC environment. We are collecting feedback and information on user experience while
            the development team continues to improve the platform for these workflows. 
            Please provide feedback via the <a href='https://docs.google.com/forms/d/e/1FAIpQLSdocu9Aq4lUaoYSZ0p9d4e1hg1U1dEBOzLjkZxgtaTMVYPpXA/viewform' 
            target='_blank' rel="noreferrer">feedback form</a> and email issues to <a href="mailto:nmdc-edge@lanl.gov?subject=NMDC EDGE issues">nmdc-edge@lanl.gov</a>.
            </p>
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left" style={{ fontStyle: 'italic' }}>
              For this beta version, a few datasets are provided in the public data folder for testing purposes or users can upload their own data files. Users are restricted to uploading a total of 150GB of data.
            </p>
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              While the results from the workflows are comparable to results for other datasets already found in the NMDC Data Portal, the results from NMDC
              EDGE cannot yet be uploaded to the NMDC Data Portal until the NMDC data registry and API are finalized. A feature within NMDC EDGE will become
              available to register data with the NMDC, together with corresponding metadata and NMDC compliant data products.
            </p>
            <br></br><br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              LA-UR-21-21661
            </p>
          </div>
          <br></br><br></br>
        </Col>
      </Row>
    </div>
  );
}

export default Home;
