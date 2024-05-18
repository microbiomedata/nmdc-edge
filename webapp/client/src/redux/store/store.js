import { createStore, applyMiddleware, compose } from "redux";
import thunk from "redux-thunk";
import rootReducer from "../reducers";
// import {createLogger} from 'redux-logger';

// const logger = createLogger({
//     /* https://github.com/evgenyrodionov/redux-logger */
//     collapsed: true,
//     diff: true
// });

const initialState = {};
//const middleware = [thunk, logger];
const middleware = [thunk];

const store = createStore(
    rootReducer,
    initialState,
    compose(
        applyMiddleware(...middleware),
    )
);

export default store;