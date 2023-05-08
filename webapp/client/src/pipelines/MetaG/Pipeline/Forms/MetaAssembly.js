import React, { useState, useEffect } from 'react';
import {
    Card,
} from 'reactstrap';

import { Header } from '../../../Common/Forms/CardHeader';
import { initialMetaAssembly } from '../Defaults';

export function MetaAssembly(props) {

    const [form, setState] = useState({ ...initialMetaAssembly });
    const [collapseParms, setCollapseParms] = useState(true);

    const setNewState2 = (name, value) => {
        setState({
            ...form,
            [name]: value
        });
    }

    const setOnoff = (stats) => {
        setNewState2("paramsOn", stats);
    }

    useEffect(() => {
        props.setParams(form, props.name);
    }, [form.paramsOn]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Card className='workflow-card'>
            <Header toggle={false} title={props.full_name} collapseParms={collapseParms}
                onoff={true} setOnoff={setOnoff} setCollapseParms={setCollapseParms} paramsOn={form.paramsOn} />
        </Card>
    );
}


