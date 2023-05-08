import React from "react";
import { Route, Redirect } from "react-router-dom";
import { connect } from "react-redux";
import PropTypes from "prop-types";

const PrivateRoute = ({ component: Component, user, ...rest }) => {
    //console.log(rest)
    return (
        <Route
            {...rest}
            render={props =>
                user.isAuthenticated === true ? (
                    <Component {...props} />
                ) : (
                        <Redirect to={{
                            pathname: '/login',
                            state: { from: rest.location.pathname+rest.location.search }
                        }} />
                    )
            }
        />
    );
}

PrivateRoute.propTypes = {
    user: PropTypes.object.isRequired
};

const mapStateToProps = state => ({
    user: state.user
});

export default connect(mapStateToProps)(PrivateRoute);