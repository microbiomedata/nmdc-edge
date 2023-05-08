import React from 'react';
import {
  CDropdown,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
} from '@coreui/react';
import CIcon from '@coreui/icons-react';

import Avatar from 'react-avatar';

const TheHeaderDropdown = (props) => {

  const userName = props.user.profile.firstname + " " + props.user.profile.lastname;
  const onLogoutClick = (e) => {
    e.preventDefault();
    props.logout();
  };

  return (
    <CDropdown inNav className="c-header-nav-items mx-2" direction="down" >
      <CDropdownToggle className="c-header-nav-link" caret={false}>
        <div className="c-avatar">
          <Avatar name={userName} color="#6A9E5D" size="40" round={true} />
        </div>
      </CDropdownToggle>
      <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownItem header tag="div" color="secondary" className="text-center" >
          <strong>Projects</strong>
        </CDropdownItem>
        <CDropdownItem to="/user/projectlist" >
          <CIcon name="cil-grid" className="mfe-2" />
          My Projects
        </CDropdownItem>
        <CDropdownItem to="/user/allprojectlist" >
          <CIcon name="cil-grid" className="mfe-2" />
          All Projects Available to Me
        </CDropdownItem>
        <CDropdownItem to="/user/jobqueue" >
          <CIcon name="cil-list-numbered" className="mfe-2" />
          Job Queue
        </CDropdownItem>
        {(!process.env.REACT_APP_FILEUPLOAD || process.env.REACT_APP_FILEUPLOAD.toLowerCase() !== 'off') && <>
          <CDropdownItem header tag="div" color="secondary" className="text-center" >
            <strong>Files</strong>
          </CDropdownItem>
          <CDropdownItem to="/user/uploadfiles" >
            <CIcon name="cil-cloud-upload" className="mfe-2" />
          Upload Files
        </CDropdownItem>
          <CDropdownItem to="/user/files" >
            <CIcon name="cil-layers" className="mfe-2" />
          Manage Uploads
        </CDropdownItem>
        </>
        }
        {props.user.profile.type === 'admin' && <>
          <CDropdownItem header tag="div" color="secondary" className="text-center" >
            <strong>Admin Tools</strong>
          </CDropdownItem>
          <CDropdownItem to="/admin/projectlist" >
            <CIcon name="cil-list" className="mfe-2" />
            Manage Projects
          </CDropdownItem>
          {(!process.env.REACT_APP_FILEUPLOAD || process.env.REACT_APP_FILEUPLOAD.toLowerCase() !== 'off') && <>
            <CDropdownItem to="/admin/filelist" >
              <CIcon name="cil-layers" className="mfe-2" />
            Manage Uploads
          </CDropdownItem>
          </>
          }
          <CDropdownItem to="/admin/userlist" >
            <CIcon name="cil-people" className="mfe-2" />
            Manage Users
          </CDropdownItem>
        </>}
        <CDropdownItem header tag="div" color="secondary" className="text-center" >
          <strong>Account</strong>
        </CDropdownItem>
        <CDropdownItem to="/user/profile" >
          <CIcon name="cil-user" className="mfe-2" />
          Profile
        </CDropdownItem>
        <CDropdownItem onClick={onLogoutClick}>
          <CIcon name="cil-account-logout" className="mfe-2" />
          Logout
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  )
}

export default TheHeaderDropdown
