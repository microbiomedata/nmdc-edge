import React from 'react';

const ProductsDropdown = (props) => {
  return (
    <>
      <div className="nmdc-header-nav-link" >
        PRODUCTS
        <button className="nmdc-header-chevron"> </button>
        <div className="nmdc-header-dropdown-menu" >
          <a title="Data Portal" href="https://data.microbiomedata.org/">
            Data Portal
          </a>
          <a title="Submission Portal" href="https://data.microbiomedata.org/submission/home">
            Submission Portal
          </a>
          <a className='nmdc-edge-link' title="NMDC EDGE" href="https://nmdc-edge.org/">
            NMDC EDGE
          </a>
          <a title="Field Notes Mobile App" href="https://microbiomedata.org/field-notes/">
            Field Notes Mobile App
          </a>
        </div>
      </div>
    </>
  )
}

export default ProductsDropdown
