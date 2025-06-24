import React from 'react'
import CIcon from '@coreui/icons-react'

const _nav = [
  {
    _tag: 'CSidebarNavItem',
    name: 'NMDC EDGE',
    to: '/home',
    icon: <CIcon name="cilHome" customClasses="c-sidebar-nav-icon" />
  },
  {
    _tag: 'CSidebarNavDropdown',
    name: 'Documentation',
    icon: 'cilStar',
    _children: [
      {
        _tag: 'CSidebarNavItem',
        name: 'Quick Start Guide',
        component: 'a',
        href: 'https://docs.microbiomedata.org/howto_guides/run_workflows/',
        target: '_blank',
        rel: 'noopener noreferrer'
      },
      {
        _tag: 'CSidebarNavItem',
        name: 'Tutorial Walkthrough',
        component: 'a',
        href: 'https://docs.microbiomedata.org/tutorials/run_workflows/',
        target: '_blank',
        rel: 'noopener noreferrer'
      },
      {
        _tag: 'CSidebarNavItem',
        name: 'Workflow Documentation',
        component: 'a',
        href: 'https://docs.microbiomedata.org/workflows/index.html',
        target: '_blank',
        rel: 'noopener noreferrer'
      }
    ],
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
      {
        _tag: 'CSidebarNavItem',
        name: 'Bulk Submission',
        to: '/metag/bulksubmission',
      },
    ],
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Metatranscriptomics',
    icon: 'cilCursor',
    to: '/metat/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Metaproteomics',
    icon: 'cilCursor',
    to: '/metap/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Natural Organic Matter',
    icon: 'cilCursor',
    to: '/organicm/workflow',
  },
  {
    _tag: 'CSidebarNavItem',
    name: 'Viruses and Plasmids',
    icon: 'cilCursor',
    to: '/virus_plasmid/workflow',
  },
]

export default _nav
