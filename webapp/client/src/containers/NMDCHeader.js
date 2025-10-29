import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  CHeader,
  CToggler,
  CHeaderNav,
} from '@coreui/react';
import { FaUserCircle } from "react-icons/fa";
import { MdLogout } from "react-icons/md";
import logo from '../assets/img/NMDC_logo_long.jpeg';

import AboutDropdown from './AboutDropdown'
import ProductsDropdown from './ProductsDropdown'
import ResourcesDropdown from './ResourcesDropdown'
import PartnerDropdown from './PartnerDropdown'
import NewsDropdown from './NewsDropdown'
import OrcidLoginHelp from '../common/UM/Common/OrcidLoginHelp';
import { setSidebar, logout } from "../redux/actions/userActions";

const NMDCHeader = (props) => {
  const dispatch = useDispatch()
  const user = useSelector(state => state.user)
  const sidebar = useSelector(state => state.sidebar)
  const [orcidid, setOrcidid] = useState();

  const toggleSidebarMobile = () => {
    const val = [false, 'responsive'].includes(sidebar.sidebarShow) ? true : 'responsive'
    dispatch(setSidebar(val))
  }

  const signOut = (e) => {
    dispatch(logout());
    props.history.push('/home')
  }

  useEffect(() => {
    //get user's orcid id
    if(user.isAuthenticated) {
      setOrcidid(user.profile.email.split('@')[0]);
    }
  }, [user]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <CHeader className={'nmdc-header'}>
      <CToggler
        inHeader
        className="ml-md-3 d-lg-none"
        onClick={toggleSidebarMobile}
      />
      <a href="https://microbiomedata.org/" className="nmdc-header-logo">
        <img style={{ width: 160, height: 55 }} src={logo} alt="Home page" />
      </a>

      <CHeaderNav className="d-md-down-none mr-auto">
      </CHeaderNav>
      <CHeaderNav>
        <AboutDropdown />
      </CHeaderNav>
      <CHeaderNav >
        <ProductsDropdown />
      </CHeaderNav>
      <CHeaderNav >
        <ResourcesDropdown />
      </CHeaderNav>
      <CHeaderNav >
        <PartnerDropdown />
      </CHeaderNav>
      <CHeaderNav >
        <NewsDropdown />
      </CHeaderNav>
      <CHeaderNav>
        <div className='nmdc-header-vr nmdc-header-no-min'></div>
      </CHeaderNav>
      {user.isAuthenticated ? (
        <>
          <CHeaderNav className="nmdc-header-orcid" style={{ paddingRight: '0px' }}>
            <a href={"https://orcid.org/" + orcidid} >
              <span className="nmdc-header-no-min" >
                <FaUserCircle size={16} className="nmdc-header-orcid-icon mfe-2" />
                {user.profile.firstname} {user.profile.lastname}
              </span>
              <img alt="OrcId logo" style={{ paddingLeft: '12px' }} src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" className="nmdc-header-orcid-img mr-2" />
            </a>
          </CHeaderNav>
          <CHeaderNav className="nmdc-header-orcid" onClick={signOut}>
            <MdLogout size={24} className="nmdc-header-orcid-icon mfe-2" />
          </CHeaderNav>
        </>
      ) : (
        <>
          <CHeaderNav className="nmdc-header-orcid nmdc-header-orcid-login">
            <a href="/disabled" >
              <img alt="OrcId login" src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" className="nmdc-header-orcid-img mr-2" />
              OrcID Login
            </a>
            <div className='nmdc-header-orcid-login-help'>
              <OrcidLoginHelp />
            </div>
          </CHeaderNav>
        </>
      )
      }

    </CHeader>
  )
}

export default NMDCHeader
