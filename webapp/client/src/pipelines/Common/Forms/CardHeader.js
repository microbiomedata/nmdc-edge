import React, { useState } from 'react';
import {
    Button, ButtonGroup, CardHeader
} from 'reactstrap';
import CIcon from '@coreui/icons-react';
import { colors } from '../../../common/Colors';

export function Header(props) {
    const [headerColor, setHeaderColor] = useState(colors.light);

    return (
        <CardHeader style={{ backgroundColor: headerColor, border: '1px' }} onMouseEnter={(e) => setHeaderColor(colors.secondary)}
            onMouseLeave={() => setHeaderColor(colors.light)}>
            {props.toggle ?
                <>
                    <span className="edge-card-header-action" data-target="#collapseParameters" onClick={props.toggleParms}>
                        {props.collapseParms ?
                            <CIcon name="cil-chevron-bottom" className="mfe-2" />
                            :
                            <CIcon name="cil-chevron-top" className="mfe-2" />
                        }
                    </span>
                &nbsp;&nbsp;&nbsp;
                </>
                :
                <>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                </>
            }
            <span className="edge-card-header-title">{props.title}</span>
            {props.onoff &&
                <ButtonGroup style={{ float: 'right' }} className="mr-3" aria-label="First group" size="sm">
                    <Button color="outline-primary" onClick={() => props.setOnoff(true)}
                        active={props.paramsOn}>On</Button>
                    <Button color="outline-primary" onClick={() => { props.setOnoff(false); props.setCollapseParms(true) }}
                        active={!props.paramsOn}>Off</Button>
                </ButtonGroup>
            }
        </CardHeader>
    );
}
