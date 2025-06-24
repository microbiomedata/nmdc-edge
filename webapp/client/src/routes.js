import React from 'react';

const Home = React.lazy(() => import('./pipelines/Home'));
const PublicProjectList = React.lazy(() => import('./common/UM/Public/ProjectList'));
const PublicProjectPage = React.lazy(() => import('./pipelines/Common/Results/ProjectPage/Public'));
const tempLogin = React.lazy(() => import('./common/UM/User/Login'));
// const UserActivate = React.lazy(() => import('./common/UM/User/Activate'));
// const UserRegister = React.lazy(() => import('./common/UM/User/Register'));
// const UserResetpassword = React.lazy(() => import('./common/UM/User/Resetpassword'));
const OAuth = React.lazy(() => import('./common/UM/Common/OrcidLogin'));

// https://github.com/ReactTraining/react-router/tree/master/packages/react-router-config
const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/home', name: 'Home', component: Home },
  { path: '/public/projectlist', name: 'ProjectList', component: PublicProjectList },
  { path: '/public/project', name: 'ProjectPage', component: PublicProjectPage },
  { path: '/nmdcedgeadminlogin', exact: true, name: 'tempLogin', component: tempLogin },
  // { path: '/activate', exact: true, name: 'Activate', component: UserActivate },
  // { path: '/register', exact: true, name: 'Register', component: UserRegister },
  // { path: '/resetpassword', exact: true, name: 'Resetpassword', component: UserResetpassword },
  { path: '/oauth', name: 'OAuth', component: OAuth },

];

export default routes;
