import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';

import jwt_decode from "jwt-decode";
import { setAuthToken } from "./common/util";
import { setCurrentUser, logout } from "./redux/actions/userActions";

import { Provider } from "react-redux";
import store from "./redux/store/store";

import './scss/style.scss';

const loading = (
  <div className="pt-3 text-center">
    <div className="sk-spinner sk-spinner-pulse">Loading</div>
  </div>
)

// Check for token to keep user logged in
if (localStorage.jwtToken) {
  // Set auth token header auth
  const token = localStorage.jwtToken;
  setAuthToken(token);
  // Decode token and get user info and exp
  const decoded = jwt_decode(token);
  // Set user and isAuthenticated
  store.dispatch(setCurrentUser(decoded));
} else {
  store.dispatch(logout());
}
//logout all tabs
window.addEventListener('storage', e => {
  if (e.key === 'jwtToken' && e.oldValue && !e.newValue) {
    store.dispatch(logout());
  }
});

// Containers
const TheLayout = React.lazy(() => import('./containers/TheLayout'));


class App extends Component {

  constructor(props) {
    super(props);
    this.events = [
      "load",
      "mousemove",
      "mousedown",
      "click",
      "scroll",
      "keypress"
    ];
    this.logout = this.logout.bind(this);
    this.resetTimeout = this.resetTimeout.bind(this);
  }

  addTimeout() {
    for (var i in this.events) {
      window.addEventListener(this.events[i], this.resetTimeout);
    }

    this.setTimeout();
  }

  clearTimeout() {
    if (this.logoutTimeout) clearTimeout(this.logoutTimeout);
  }

  setTimeout() {
    // 3600 * 1000 = 60mins
    this.logoutTimeout = setTimeout(this.logout, 3600 * 1000);
  }

  resetTimeout() {
    this.clearTimeout();
    this.setTimeout();
  }

  logout() {
    alert("You've been logged out due to inactivity.");
    // Send a logout request to the API
    store.dispatch(logout());
    // Redirect to home
    window.location.href = "/home";
    this.destroy(); // Cleanup
  }

  destroy() {
    this.clearTimeout();

    for (var i in this.events) {
      window.removeEventListener(this.events[i], this.resetTimeout);
    }
  }

  componentDidMount() {
    // If logged in, add timeout
    if (localStorage.jwtToken) {
      this.addTimeout();
    }
  }

  render() {
    return (
      <Provider store={store}>
        <Router>
          <React.Suspense fallback={loading}>
            <Switch>
              <Route path="/" name="Home" render={props => <TheLayout {...props} />} />
            </Switch>
          </React.Suspense>
        </Router>
      </Provider>
    );
  }
}

export default App;
