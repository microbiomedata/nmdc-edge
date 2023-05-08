import React, { useState } from 'react';
import ReactTooltip from "react-tooltip";
import { FaInfoCircle } from "react-icons/fa";

export const MyTooltip = props => {
    const [showTooltip, setShowTooltip] = useState(props.showTooltip);

    return (
        <>
            <span data-tip='' data-for={props.id} data-html={true} data-event={props.event ? props.event : ''}
                 data-effect='solid' className={props.className}
                onMouseOver={e => setShowTooltip(true)} onMouseLeave={e => {if(!props.showTooltip) setShowTooltip(false)}}>
                {props.text} &nbsp;
                <span className={showTooltip ? "" : "hide"}><FaInfoCircle /></span>
            </span>
            <ReactTooltip globalEventOff='click' wrapper="span" id={props.id} type={props.type} place={props.place}>
                {props.tooltip}
            </ReactTooltip>
        </>
    );
};

export const WarningTooltip = props => {

    return (
        <>
            <span data-tip='' data-for={props.id} data-html={true}
                data-place="right" data-effect='solid' >
                <span className="edge-form-input-error"></span></span>
            <ReactTooltip wrapper="span" id={props.id} >
                {props.tooltip}
            </ReactTooltip>
        </>
    );
};

export default MyTooltip;