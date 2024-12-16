import React from 'react';

const ResourcesDropdown = (props) => {
  return (
    <>
      <div className="nmdc-header-nav-link" >
        Resources
        <button className="nmdc-header-chevron"> </button>
        <div className="nmdc-header-dropdown-menu" >
          <a title="Data Standards" href="https://microbiomedata.org/data-standards/">
            Data Standards
          </a>
          <a title="Bioinformatics Workflows" href="https://microbiomedata.org/workflows/">
            Bioinformatics Workflows
          </a>
          <a title="GitHub" href="https://github.com/microbiomedata">
            GitHub
          </a>
          <a title="Documentation" href="https://microbiomedata.org/documentation/">
            Documentation
          </a>
          <a title="Data Management" href="https://microbiomedata.org/data-management/">
            Data Management
          </a>
          <a title="Data Integration" href="https://microbiomedata.org/data-integration/">
            Data Integration
          </a>
        </div>
      </div>
    </>
  )
}

export default ResourcesDropdown
