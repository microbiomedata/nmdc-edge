import React from 'react';

const PartnerDropdown = (props) => {
  return (
    <>
      <div className="nmdc-header-nav-link nmdc-header-nav-link-no-min" >
        Get Involved
        <button className="nmdc-header-chevron"> </button>
        <div className="nmdc-header-dropdown-menu" >
          <a title="Community" href="https://microbiomedata.org/community/">
            Community
          </a>
          <a title="Ambassadors" href="https://microbiomedata.org/ambassadors/">
            Ambassadors
          </a>
          <a title="Champions" href="https://microbiomedata.org/community/championsprogram/">
            Champions
          </a>
          <a title="User Research" href="https://microbiomedata.org/user-research/">
            User Research
          </a>
        </div>
      </div>
    </>
  )
}

export default PartnerDropdown
