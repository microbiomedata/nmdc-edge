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
            The National Microbiome Data Collaborative (<a href='https://microbiomedata.org/' target='_blank' rel="noreferrer">NMDC</a>) supports a Findable, Accessible, 
            Interoperable, and Reusable (FAIR) microbiome data sharing network through infrastructure, data standards, and community building to address pressing challenges 
            in environmental sciences. The NMDC EDGE (Empowering the Development of Genomics Expertise) platform was created so that all researchers can access and process 
            their ‘omics data using the NMDC standardized bioinformatics workflows, regardless of resource availability or expertise level. All microbiome datasets in 
            the <a href='https://data.microbiomedata.org/' target='_blank' rel="noreferrer">NMDC Data Portal</a> have been processed using the same workflows as those housed 
            in NMDC EDGE, allowing datasets to be directly compared between the two interfaces.
            </p>
            <br></br>
            <p className="edge-text-font edge-text-size-large float-left">
            A <a href={process.env.REACT_APP_API_URL + "/docs/help/quickStart.pdf"} target="_blank" rel="noreferrer">Quick Start Guide</a> along with 
            other <a href={"/tutorial"} target="_blank" rel="noreferrer">Tutorials and User Guides</a> are available for running workflows in NMDC EDGE. 
            The full <a href='https://nmdc-documentation.readthedocs.io/en/latest/index.html' target='_blank' rel="noreferrer">NMDC documentation site</a> provides more specific 
            information about the NMDC workflows and their associated tools and parameters. NMDC EDGE can either be installed locally 
            or the workflows can be run online using shared NMDC computing resources.
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
