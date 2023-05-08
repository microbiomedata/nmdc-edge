import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import {
  CCreateElement,
  CSidebar,
  CSidebarBrand,
  CSidebarNav,
  CSidebarNavDivider,
  CSidebarNavTitle,
  CSidebarMinimizer,
  CSidebarNavDropdown,
  CSidebarNavItem,
} from '@coreui/react'

import CIcon from '@coreui/icons-react'

// sidebar nav config
import navigation from './_nav';
import logo from '../assets/img/brand/logo.png'

import { setSidebar } from "../redux/actions/userActions";

const TheSidebar = () => {
  const dispatch = useDispatch()
  const sidebar = useSelector(state => state.sidebar)

  return (
    <CSidebar
      show={sidebar.sidebarShow}
      onShowChange={(val) => dispatch(setSidebar(val))}
    >
      <CSidebarBrand className="d-md-down-none" to="/home">
        <CIcon
          className="c-sidebar-brand-full"
          src={logo}
          height={40}
        />
        <CIcon
          className="c-sidebar-brand-minimized"
          src={logo}
          height={20}
        />
      </CSidebarBrand>
      <CSidebarNav>

        <CCreateElement
          items={navigation}
          components={{
            CSidebarNavDivider,
            CSidebarNavDropdown,
            CSidebarNavItem,
            CSidebarNavTitle
          }}
        />
      </CSidebarNav>
      <CSidebarMinimizer className="c-d-md-down-none"/>
    </CSidebar>
  )
}

export default React.memo(TheSidebar)
