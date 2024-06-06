import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme } from '../../../../common/table';

function TopMolecules(props) {
    const [moleculeData, setmoleculeData] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);

    const moleculeColumns = [
        {
            title: 'Index', field: 'Index',
        },
        {
            title: 'm/z', field: 'm/z', 
        },
        {
            title: 'Calibrated m/z', field: 'Calibrated m/z',
        },
        {
            title: 'Calculated m/z', field: 'Calculated m/z', 
        },
        {
            title: 'Peak Height', field: 'Peak Height',
        },
        {
            title: 'Resolving Power', field: 'Resolving Power',
        },
        {
            title: 'S/N', field: 'S/N',
        },
        {
            title: 'Ion Charge', field: 'Ion Charge',
        },
        {
            title: 'm/z Error (ppm)', field: 'm/z Error (ppm)', 
        },
        {
            title: 'm/z Error Score', field: 'm/z Error Score',
        },
        {
            title: 'Isotopologue Similarity', field: 'Isotopologue Similarity', hidden: true
        },
        {
            title: 'Confidence Score', field: 'Confidence Score', hidden: true
        },
        {
            title: 'DBE', field: 'DBE', hidden: true
        },
        {
            title: 'H/C', field: 'H/C', hidden: true
        },
        {
            title: 'O/C', field: 'O/C', hidden: true
        },
        {
            title: 'Heteroatom Class', field: 'Heteroatom Class', hidden: true
        },
        {
            title: 'Ion Type', field: 'Ion Type', hidden: true
        },
        {
            title: 'Is Isotopologue', field: 'Is Isotopologue', hidden: true
        },
        {
            title: 'Mono Isotopic Index', field: 'Mono Isotopic Index', hidden: true
        },
        {
            title: 'Molecular Formula', field: 'Molecular Formula', hidden: false
        },
        {
            title: 'C', field: 'C', hidden: true
        },
        {
            title: 'H', field: 'H', hidden: true
        },
        {
            title: 'O', field: 'O', hidden: true
        },
        {
            title: '13C', field: '13C', hidden: true
        },
        {
            title: '18O', field: '18O', hidden: true
        },
        {
            title: '17O', field: '17O', hidden: true
        },
    ];
    //componentDidMount()
    useEffect(() => {
        let molecules = props.result.top_molecules.map(obj => {
            //console.log(obj)
            let rObj = obj

            return rObj;
        });

        setmoleculeData(molecules);

    }, [props.result]);

    return (
        <>
            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    title="Top_molecules"
                    columns={moleculeColumns}
                    icons={tableIcons}
                    data={moleculeData}
                    options={{
                        exportButton: false,
                        exportFileName: 'NOM_top_molecules',
                        columnsButton: true,
                        grouping: false,
                        search: true,
                        paging: true,
                        pageSize: 5,
                        pageSizeOptions: [5, 10, 20, 50, 100],
                        emptyRowsWhenPaging: false,
                        showTitle: true,
                        rowStyle: rowData => ({
                          backgroundColor: (selectedRow === rowData.tableData.id) ? '#EEE' : '#FFF'
                        })
                    }}
                    onRowClick={((evt, selectedRow) => setSelectedRow(selectedRow.tableData.id))}
                />
            </MuiThemeProvider>
            <br></br><br></br>
        </>

    );
}

export default TopMolecules;
