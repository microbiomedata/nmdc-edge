import React from 'react';

const NewsDropdown = (props) => {
  return (
    <>
      <div className="nmdc-header-nav-link nmdc-header-nav-link-no-min" >
        News &amp; Impact
        <button className="nmdc-header-chevron"> </button>
        <div className="nmdc-header-dropdown-menu" >
          <a title="Annual Reports" href="https://microbiomedata.org/annual_report/">
            Annual Reports
          </a>
          <a title="Blog" href="https://microbiomedata.org/blog/">
            Blog
          </a>
          <a title="Events" href="https://microbiomedata.org/events/">
            Events
          </a>
          <a title="Media Materials" href="https://microbiomedata.org/media/">
            Media Materials
          </a>
          <a title="Newsletters" href="https://microbiomedata.org/newsletters/">
            Newsletters
          </a>
          <a title="Publications" href="https://microbiomedata.org/publications/">
            Publications
          </a>
        </div>
      </div>
    </>
  )
}

export default NewsDropdown
