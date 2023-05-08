import { combineReducers } from "redux";
import userReducer from "./userReducer";
import errorReducer from "./errorReducer";
import messageReducer from "./messageReducer";
import pageReducer from "./pageReducer";
import sidebarReducer from './sidebarReducer';

export default combineReducers({
    user: userReducer,
    errors: errorReducer,
    messages: messageReducer,
    page: pageReducer,
    sidebar: sidebarReducer,
});
