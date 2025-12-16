import React from 'react';
import { Col, Row } from 'reactstrap';
import config from "../config";
import workflows from '../assets/img/nmdc-edge-workflows.png';

function Home() {
  //set to home for all public routes after logged in
  localStorage.setItem("loginFrom", "/home");

  return (
    <div className="animated fadeIn nmdc-edge-home">
      <Row className="justify-content-center">
        <Col xs="12" sm="12" md="12">
          <div className="clearfix">
            <br></br>
            <p style={{ color: 'blue' }}className="edge-text-font edge-text-size-large float-left">
              Due to a shift in project budget and priorities, we will no longer support running workflows in NMDC EDGE beyond February 12th, 2026. Users will be able to 
              view their previously run projects until January 2027; however, no new projects will be run on nmdc-edge.org beyond Feb. 12th, 2026. We encourage users to 
              download the results of existing projects before the data is removed. 
              To ensure continued access and discoverability, users are also encouraged to submit their microbiome data (along with sample metadata) through the 
              <a href='https://data.microbiomedata.org/submission/home' target='_blank' rel="noreferrer">NMDC Submission Portal</a>. 
              Processed data submitted in this way will be made available through the  . 
              We will be incorporating the NMDC workflows into the original EDGE bioinformatics platform so that users can continue running standardized multi-omics microbiome 
              workflows.Thank you for your interest, contributions, and usage of this site.
              For any issues or questions that require support from a team member, please contact nmdc-edge@lanl.gov.
            </p>
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              Access the detailed <a href='https://docs.microbiomedata.org/howto_guides/run_workflows/' target='_blank' rel="noreferrer">Quick Start Guide</a>, <a href='https://docs.microbiomedata.org/tutorials/run_workflows/' target='_blank' rel="noreferrer">Video Tutorial</a>, and <a href='https://docs.microbiomedata.org/workflows/index.html' target='_blank' rel="noreferrer">Workflow Documentation</a> through 
              the full <a href='https://docs.microbiomedata.org/' target='_blank' rel="noreferrer">NMDC documentation site</a> (also available via the Documentation tab on the left menu bar or under Resources at the top banner).  
            </p>
            <br></br><br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              We are continuously collecting feedback and information on user experiences with the workflows and the NMDC EDGE platform. Please provide feedback via
              this <a href='https://forms.gle/rMhjPj8PoyhhWWKD8' target='_blank' rel="noreferrer">feedback form</a>.
            </p>
            <br></br><br></br>
            <p className="edge-text-font edge-text-size-large float-left">
              For any issues or questions that require support from a team member, please contact <i>nmdc-edge@lanl.gov</i> or open an issue
              on <a href='https://github.com/microbiomedata/nmdc-edge' target='_blank' rel="noreferrer">GitHub</a>.
            </p>
            <br></br><br></br>
          </div>
          <div className='edge-center'>
            <img alt="dtra logo" style={{ width: 900, height: 600 }} src={workflows} />
          </div>
          <br></br><br></br>
          <p className="edge-text-font edge-text-size-large float-left">
            LA-UR-21-21661
          </p>
          <br></br><br></br>
        </Col>
      </Row>
    </div>
  );
}

export default Home;
