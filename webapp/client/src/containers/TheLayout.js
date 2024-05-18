import React from 'react'
import {
  TheContent,
  TheSidebar,
  NMDCHeader
} from './index'

const TheLayout = (props) => {

  return (
    <div className="c-app c-default-layout">
      <TheSidebar/>
      <div className="c-wrapper">
        <NMDCHeader {...props}/>
        <div className="c-body">
          <TheContent/>
        </div>
      </div>
    </div>
  )
}

export default TheLayout
