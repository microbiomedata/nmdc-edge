import { SIDEBAR_SET } from "../actions/types";

const initialState = {
    sidebarShow: 'responsive'
}

const sidebarReducer = function (state = initialState, action) {
    switch (action.type) {
        case SIDEBAR_SET:
            return {
                ...state,
                sidebarShow: action.payload
            };
        default:
            return state
    }
}

export default sidebarReducer;