import React from 'react'
import CIcon from '@coreui/icons-react'

const _nav = [
  {
    _tag: 'CSidebarNavItem',
    name: 'Home',
    to: '/home',
    icon: <CIcon name="cilHome" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Tutorials',
    to: '/tutorial',
    icon: <CIcon name="cilStar" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Public Projects',
    to: '/public/projectlist',
    icon: <CIcon name="cilGrid" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Upload Files',
    to: '/user/files',
    icon: <CIcon name="cilCloudUpload" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Retrieve SRA Data',
    to: '/sra/data',
    icon: <CIcon name="cilCloudUpload" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavTitle',
    _children: ['NMDC'],
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'NMDC Home',
    target: '_blank',
    href: 'https://microbiomedata.org/',
    icon: <CIcon name="cilExternalLink" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Sample Submission Portal',
    target: '_blank',
    href: 'https://data.microbiomedata.org/submission/home',
    icon: <CIcon name="cilExternalLink" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Data Portal',
    target: '_blank',
    href: 'https://data.microbiomedata.org/',
    icon: <CIcon name="cilExternalLink" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Documentation',
    target: '_blank',
    href: 'https://nmdc-documentation.readthedocs.io/en/latest/index.html',
    icon: <CIcon name="cilExternalLink" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavTitle',
    _children: ['Workflows'],
  },

  {
    _tag: 'CSidebarNavDropdown',
    name: 'Metagenomics',
    icon: 'cilLayers',
    _children: [
      {
        _tag: 'CSidebarNavItem',
        name: 'Run a Single Workflow',
        to: '/metag/workflow',
      },
      {
        _tag: 'CSidebarNavItem',
        name: 'Run Multiple Workflows',
        to: '/metag/pipeline',
      },
    ],
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Metatranscriptome',
    icon: 'cilChevronRight',
    to: '/metat/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Metaproteomics',
    icon: 'cilChevronRight',
    to: '/metap/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Natural Organic Matter',
    icon: 'cilChevronRight',
    to: '/organicm/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Viruses and Plasmids',
    icon: 'cilChevronRight',
    to: '/virus_plasmid/workflow',
  },
]

export default _nav
