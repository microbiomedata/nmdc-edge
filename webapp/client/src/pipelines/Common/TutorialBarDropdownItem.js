import React from 'react';
import {
    CDropdownItem,
} from '@coreui/react';

function TutorialBarDropdownItem(props) {
    return (
        <>
            {
                Object.keys(props.items).map((item, index) => {
                    return (
                        <CDropdownItem href={props.url + props.items[item]} target="_blank" key={index} >
                            {item}
                        </CDropdownItem>
                    )
                })
            }
        </>
    );
}

export default TutorialBarDropdownItem;