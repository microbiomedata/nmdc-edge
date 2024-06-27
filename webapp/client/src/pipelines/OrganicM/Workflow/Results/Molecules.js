import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, handleTableNumberFilter } from '../../../../common/table';

function Molecules(props) {
    const [moleculeData, setmoleculeData] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);
    const moleculeColumns = [
        {
            title: 'Index', field: 'Index', filtering: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Index']),
        },
        {
            title: 'm/z', field: 'm/z',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['m/z']),
        },
        {
            title: 'Calibrated m/z', field: 'Calibrated m/z', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Calibrated m/z']),
        },
        {
            title: 'Calculated m/z', field: 'Calculated m/z', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Calculated m/z']),
        },
        {
            title: 'Peak Height', field: 'Peak Height',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Peak Height']),
        },
        {
            title: 'Resolving Power', field: 'Resolving Power',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Resolving Power']),
        },
        {
            title: 'S/N', field: 'S/N',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['S/N']),
        },
        {
            title: 'Ion Charge', field: 'Ion Charge', hidden: true
        },
        {
            title: 'm/z Error (ppm)', field: 'm/z Error (ppm)', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['m/z Error (ppm)']),
        },
        {
            title: 'm/z Error Score', field: 'm/z Error Score', hidden: false,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['m/z Error Score']),
        },
        {
            title: 'Isotopologue Similarity', field: 'Isotopologue Similarity', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Isotopologue Similarity']),
        },
        {
            title: 'Confidence Score', field: 'Confidence Score', hidden: false,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Confidence Score']),
        },
        {
            title: 'DBE', field: 'DBE', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['DBE']),
        },
        {
            title: 'H/C', field: 'H/C', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['H/C']),
        },
        {
            title: 'O/C', field: 'O/C', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['O/C']),
        },
        {
            title: 'Heteroatom Class', field: 'Heteroatom Class', hidden: true,
        },
        {
            title: 'Ion Type', field: 'Ion Type', hidden: true,
        },
        {
            title: 'Is Isotopologue', field: 'Is Isotopologue', hidden: true,
        },
        {
            title: 'Mono Isotopic Index', field: 'Mono Isotopic Index', hidden: true,
        },
        {
            title: 'Molecular Formula', field: 'Molecular Formula', hidden: false
        },
        {
            title: 'C', field: 'C', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['C']),
        },
        {
            title: 'H', field: 'H', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['H']),
        },
        {
            title: 'O', field: 'O', hidden: true,
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['O']),
        },
        {
            title: '13C', field: '13C', hidden: true,
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
        let molecules = props.result.molecules_json.map(obj => {
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
                    title="Molecules"
                    columns={moleculeColumns}
                    icons={tableIcons}
                    data={moleculeData}
                    options={{
                        exportButton: false,
                        exportFileName: 'NOM_top_molecules',
                        columnsButton: true,
                        grouping: false,
                        search: true,
                        filtering: true,
                        paging: true,
                        pageSize: 10,
                        pageSizeOptions: [10, 20, 50, 100],
                        emptyRowsWhenPaging: false,
                        showTitle: false,
                        rowStyle: rowData => ({
                            backgroundColor: (selectedRow === rowData.tableData.id) ? '#EEE' : '#FFF'
                        })
                    }}
                //onRowClick={((evt, selectedRow) => setSelectedRow(selectedRow.tableData.id))}
                />
            </MuiThemeProvider>
            <br></br><br></br>
        </>

    );
}

export default Molecules;
