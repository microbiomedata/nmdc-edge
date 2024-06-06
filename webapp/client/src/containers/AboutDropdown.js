import React from 'react';

const AboutDropdown = (props) => {
  return (
    <>
      <div className="nmdc-header-nav-link" >
        <a title="About Us" href="https://microbiomedata.org/about/">
          ABOUT US
        </a>
        <button className="nmdc-header-chevron"> </button>
        <div className="nmdc-header-dropdown-menu" >
          <a title="Our Story" href="https://microbiomedata.org/about/">
            Our Story
          </a>
          <a title="Team" href="https://microbiomedata.org/team/">
            Team
          </a>
          <a title="Advisory" href="https://microbiomedata.org/advisory/">
            Advisory
          </a>
          <a title="Diversity, Equity, and Inclusion" href="https://microbiomedata.org/idea-action-plan/">
            Diversity, Equity, and Inclusion
          </a>
          <a title="Data Use Policy" href="https://microbiomedata.org/nmdc-data-use-policy/">
            Data Use Policy
          </a>
          <a title="Contact Us" href="https://microbiomedata.org/contact/">
            Contact Us
          </a>
        </div>
      </div>
    </>
  )
}

export default AboutDropdown
