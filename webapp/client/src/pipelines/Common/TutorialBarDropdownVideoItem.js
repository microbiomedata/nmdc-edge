import React from 'react';
import {
    CDropdownItem,
} from '@coreui/react';

function TutorialBarDropdownVideoItem(props) {
    return (
        <>
            {
                Object.keys(props.items).map((item, index) => {
                    return (
                        //set video popup on click event
                        <CDropdownItem component="button" onClick={() => props.setItem(item, props.items[item])} key={index} >
                            {item}
                        </CDropdownItem>
                    )
                })
            }
        </>
    );
}

export default TutorialBarDropdownVideoItem;