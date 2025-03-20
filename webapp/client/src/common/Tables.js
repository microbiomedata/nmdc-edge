import React from 'react';
import { Table } from 'reactstrap';

//parse json data to table
export function JsonTable(props) {
    return (
        <Table responsive striped size="sm">
            <thead>
                <tr>
                    {props.headers.map((header, index) => (
                        <th key={index}>{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {props.data.map((item, ind) => {
                    return (
                        <tr key={ind}>
                            {props.headers.map((header, index) => (
                                <td key={index}>{(!item[header]||isNaN(Number(item[header]))||item[header].length===0)? item[header]:Number(item[header]).toLocaleString("en-US")}</td>
                            ))}
                        </tr>
                    )
                })}
            </tbody>
        </Table>
    );
}

//parse array data to table
export function ArrayTable(props) {
    return (
        <Table responsive striped size="sm">
            <thead>
                <tr>
                    {props.headers.map((header, index) => (
                        <th key={index}>{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {props.data.map((item, ind) => {
                    return (
                        <tr key={ind}>
                            {item.map((val, index) => (
                                <td key={index}>{(!val||isNaN(Number(val))||val.length===0)? val: Number(val).toLocaleString("en-US")}</td>
                            ))}
                        </tr>
                    )
                })}
            </tbody>
        </Table>
    );
}

//parse key:value data to table
export function StatsTable(props) {
    return (
        <Table responsive striped size="sm">
            <thead>
                <tr>
                    {props.headers.map((header, index) => (
                        <th key={index}>{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {props.data && Object.keys(props.data).map((item, index) => (
                    <tr key={index} >
                        <td>{item}</td>
                        <td>{(!props.data[item]||isNaN(Number(props.data[item]))||props.data[item].length===0)? props.data[item]: Number(props.data[item]).toLocaleString("en-US")}</td>
                    </tr>
                ))}
            </tbody>
        </Table>
    );
}