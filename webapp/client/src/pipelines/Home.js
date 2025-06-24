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
            <p className="edge-text-font edge-text-size-large float-left">
              The National Microbiome Data Collaborative (<a href='https://microbiomedata.org/' target='_blank' rel="noreferrer">NMDC</a>) supports a Findable, Accessible,
              Interoperable, and Reusable (FAIR) microbiome data sharing network through infrastructure, data standards, and community building to address pressing challenges
              in environmental sciences. The NMDC EDGE (Empowering the Development of Genomics Expertise) platform was created so that all researchers can access and process
              their 'omics data using the NMDC standardized bioinformatics workflows, regardless of resource availability or expertise level. All microbiome datasets in
              the <a href='https://data.microbiomedata.org/' target='_blank' rel="noreferrer">NMDC Data Portal</a> have been processed using the same workflows as those housed
              in NMDC EDGE, allowing datasets to be directly compared between the two interfaces.
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
