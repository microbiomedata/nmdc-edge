import React, { useState, useEffect } from 'react';
import {
    Card, 
} from 'reactstrap';

import { initialReadbasedAnalysis } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';

export function ReadbasedAnalysis(props) {

    const [form, setState] = useState({ ...initialReadbasedAnalysis });
    const [collapseParms, setCollapseParms] = useState(false);

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