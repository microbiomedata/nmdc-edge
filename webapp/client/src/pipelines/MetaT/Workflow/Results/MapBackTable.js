import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, handleTableNumberFilter } from '../../../../common/table';

function MapBackTable(props) {
    const [featureData, setFeatureData] = useState([]);

    const featureColumns = [
        {
            title: 'ID', field: '#ID',
        },
        {
            title: 'Avg_fold', field: 'Avg_fold',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Avg_fold']),
        },
        {
            title: 'Length', field: 'Length',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Length']),
        },
        {
            title: 'Ref_GC', field: 'Ref_GC',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Ref_GC']),
        },
        {
            title: 'Covered_percent', field: 'Covered_percent',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Covered_percent']),
        },
        {
            title: 'Covered_bases', field: 'Covered_bases',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Covered_bases']),
        },
        {
            title: 'Plus_reads', field: 'Plus_reads',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Plus_reads']),
        },
        {
            title: 'Minus_reads', field: 'Minus_reads',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Minus_reads']),
        },
        {
            title: 'Read_GC', field: 'Read_GC',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Read_GC']),
        },
        {
            title: 'Median_fold', field: 'Median_fold',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Median_fold']),
        },
        {
            title: 'Std_Dev', field: 'Std_Dev',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['Std_Dev']),
        },
    ];
    //componentDidMount()
    useEffect(() => {
        setFeatureData(props.data);
    }, [props.data]);

    return (
        <>
            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    title="Top_MapBack"
                    columns={featureColumns}
                    icons={tableIcons}
                    data={featureData}
                    options={{
                        exportButton: false,
                        exportFileName: 'metaT_top_MapBack',
                        columnsButton: true,
                        grouping: false,
                        search: true,
                        filtering: true,
                        paging: true,
                        pageSize: 10,
                        pageSizeOptions: [10, 20, 50, 100],
                        emptyRowsWhenPaging: false,
                        showTitle: false,
                    }}
                />
            </MuiThemeProvider>
            <br></br><br></br>
        </>

    );
}

export default MapBackTable;
