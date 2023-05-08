import {
    SET_CURRENT_USER,
    SET_NEW_USER,
    USER_LOADING
} from "../actions/types";

const isEmpty = require("is-empty");
const initialState = {
    isAuthenticated: false,
    profile: {},
    loading: false
};

const userReducer = function (state = initialState, action) {
    switch (action.type) {
        case SET_CURRENT_USER:
            return {
                ...state,
                isAuthenticated: !isEmpty(action.payload),
                profile: action.payload
            };
        case SET_NEW_USER:
            return {
                ...state,
                profile: action.payload
            };
        case USER_LOADING:
            return {
                ...state,
                loading: action.payload
            };
        default:
            return state;
    }
}

export default userReducer;