import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import {
  CHeaderNavLink,
} from '@coreui/react';
import { notify } from '../common/util';
import ImportOldData from './ImportOldData';

function SubMenuBar(props) {
  const user = useSelector(state => state.user);
  const [openDialog, setOpenDialog] = useState(false);

  const handleDialogSuccess = () => {
    setOpenDialog(false);
    notify('success', 'Your old projects/uploads imported successfully!');
    setTimeout(() => window.location = "/user/projectlist", 2000);
  }
  const handleDialogClose = () => {
    setOpenDialog(false);
  }

  return (
    <span>
      {
        user.isAuthenticated ? (
          <div style={{ backgroundColor: 'white', height: '60px' }}>
            <ImportOldData
              isOpen={openDialog}
              handleSuccess={handleDialogSuccess}
              handleClickClose={handleDialogClose}
            />
            <div className="submenu" >
              <span className="nmdc-header-no-min" style={{paddingLeft:'50px'}}></span>
              <CHeaderNavLink className="nmdc-header-no-min btn btn-pill btn-ghost-info" onClick={() => { setOpenDialog(true) }}>Import Old Projects/Uploads with Email/Passsword</CHeaderNavLink>
              <CHeaderNavLink className="btn btn-pill btn-ghost-primary" to="/user/projectlist">My Projects</CHeaderNavLink>
              <CHeaderNavLink className="btn btn-pill btn-ghost-primary" to="/user/allprojectlist">All Projects Available to Me</CHeaderNavLink>
              <CHeaderNavLink className="btn btn-pill btn-ghost-primary" to="/user/jobqueue">Job Queue</CHeaderNavLink>
              <CHeaderNavLink className="nmdc-header-no-min btn btn-pill btn-ghost-primary" to="/user/profile">My Profile</CHeaderNavLink>
              {user.profile.type === 'admin' && <>
                <CHeaderNavLink className="nmdc-header-no-min btn btn-pill btn-ghost-danger" to="/admin/projectlist">Admin Projects</CHeaderNavLink>
                <CHeaderNavLink className="nmdc-header-no-min btn btn-pill btn-ghost-danger" to="/admin/filelist">Admin Uploads</CHeaderNavLink>
                <CHeaderNavLink className="nmdc-header-no-min btn btn-pill btn-ghost-danger" to="/admin/userlist">Admin Users</CHeaderNavLink>
              </>}

              <span className="nmdc-header-no-min" style={{paddingRight:'50px'}}></span>
            </div>
            <hr />
          </div>
        ) : (<></>)
      }
    </span>
  );
}

export default SubMenuBar;