import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  CHeader,
  CToggler,
  CHeaderBrand,
  CHeaderNav,
  CHeaderNavItem,
  CHeaderNavLink,
} from '@coreui/react';
import CIcon from '@coreui/icons-react';

import {
  TheHeaderDropdown,
} from './index'

import { setSidebar, logout } from "../redux/actions/userActions";

const TheHeader = (props) => {
  const dispatch = useDispatch()
  const user = useSelector(state => state.user)
  const sidebar = useSelector(state => state.sidebar)


  const toggleSidebar = () => {
    const val = [true, 'responsive'].includes(sidebar.sidebarShow) ? false : 'responsive';
    dispatch(setSidebar(val))
  }

  const toggleSidebarMobile = () => {
    const val = [false, 'responsive'].includes(sidebar.sidebarShow) ? true : 'responsive'
    dispatch(setSidebar(val))
  }

  const signOut = (e) => {
    dispatch(logout());
    props.history.push('/login')
  }

  return (
    <CHeader >
      <CToggler
        inHeader
        className="ml-md-3 d-lg-none"
        onClick={toggleSidebarMobile}
      />
      <CToggler
        inHeader
        className="ml-3 d-md-down-none"
        onClick={toggleSidebar}
      />
      <CHeaderBrand className="mx-auto d-lg-none" to="/">
        <CIcon name="logo" height="48" alt="Logo" />
      </CHeaderBrand>
      {user.isAuthenticated ? (
        <>

          <CHeaderNav className="d-md-down-none mr-auto">
            <CHeaderNavItem className="px-3" >
              <CHeaderNavLink className="edge-header-nav-link" to="/user/projectlist">My Projects</CHeaderNavLink>
            </CHeaderNavItem>
            <CHeaderNavItem className="px-3">
              <CHeaderNavLink className="edge-header-nav-link" to="/user/jobqueue">Job Queue</CHeaderNavLink>
            </CHeaderNavItem>
          </CHeaderNav>

          <CHeaderNav className="px-3">
            <TheHeaderDropdown user={user} logout={e => signOut(e)} />
          </CHeaderNav>
        </>
      ) : (
          <>
            <CHeaderNav className="px-3">
              <CHeaderNavItem className="px-3">
                <CHeaderNavLink className="edge-header-nav-link" to="/login">Login</CHeaderNavLink>
              </CHeaderNavItem>
            </CHeaderNav>
          </>
        )
      }

    </CHeader>
  )
}

export default TheHeader
