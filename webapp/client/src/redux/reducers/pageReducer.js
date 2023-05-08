import { PAGE_PATH, PAGE_LOADING, SUBMIT_FORM } from "../actions/types";

const initialState = {
    loading: false,
    submitting_form: false,
    path: null,
};

const pageReducer = function (state = initialState, action) {
    switch (action.type) {
        case PAGE_PATH:
            return {
                ...state,
                path: action.payload
            };
        case PAGE_LOADING:
            return {
                ...state,
                loading: action.payload
            };
        case SUBMIT_FORM:
            return {
                ...state,
                submitting_form: action.payload
            };
        default:
            return state;
    }
}

export default pageReducer;