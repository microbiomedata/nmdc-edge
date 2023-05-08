import { ADD_MESSAGES, CLEAN_MESSAGES } from "../actions/types";

const initialState = {};

const messageReducer = function (state = initialState, action) {
    switch (action.type) {
        case ADD_MESSAGES:
            if (action.key) {
                return {
                    ...state,
                    [action.key]: action.payload
                };
            }
            else {
                return {...state, ...action.payload};
            }
        case CLEAN_MESSAGES:
            return {};
        default:
            return state;
    }
}

export default messageReducer;