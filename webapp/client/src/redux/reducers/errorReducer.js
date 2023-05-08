import { ADD_ERRORS, CLEAN_ERRORS } from "../actions/types";

const initialState = {};

const errorReducer = function (state = initialState, action) {
    switch (action.type) {
        case ADD_ERRORS:
            if (action.key) {
                return {
                    ...state,
                    [action.key]: action.payload
                };
            }
            else {
                return {...state, ...action.payload};
            }
        case CLEAN_ERRORS:
            return {};
        default:
            return state;
    }
}

export default errorReducer;