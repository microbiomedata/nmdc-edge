import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, handleTableNumberFilter } from '../../../../common/table';

function QualitySummary(props) {
    const [featureData, setFeatureData] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);
    
    const featureColumns = [
        {
            title: 'contig_id', field: 'contig_id',
        },
        {
            title: 'contig_length', field: 'contig_length', 
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['contig_length']),
        },
        {
            title: 'provirus', field: 'provirus',
        },
        {
            title: 'proviral_length', field: 'proviral_length', 
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['proviral_length']),
        },
        {
            title: 'gene_count', field: 'gene_count',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['gene_count']),
        },
        {
            title: 'viral_genes', field: 'viral_genes',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['viral_genes']),
        },
        {
            title: 'host_genes', field: 'host_genes',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['host_genes']),
        },
        {
            title: 'checkv_quality', field: 'checkv_quality',
        },
        {
            title: 'miuvig_quality', field: 'miuvig_quality', 
        },
        {
            title: 'completeness', field: 'completeness',
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['completeness']),
        },
        {
            title: 'completeness_method', field: 'completeness_method', 
        },
        {
            title: 'contamination', field: 'contamination', 
        },
        {
            title: 'kmer_freq', field: 'kmer_freq', 
            customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['kmer_freq']),
        },
        {
            title: 'warnings', field: 'warnings', 
        },
    ];
    //componentDidMount()
    useEffect(() => {
        let features = props.result.map(obj => {
            //console.log(obj)
            let rObj = obj;

            return rObj;
        });

        setFeatureData(features);

    }, [props.result]);

    return (
        <>
            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    title=""
                    columns={featureColumns}
                    icons={tableIcons}
                    data={featureData}
                    options={{
                        exportButton: false,
                        exportFileName: 'quality',
                        columnsButton: true,
                        grouping: false,
                        search: true,
                        filtering: true,
                        paging: true,
                        pageSize: 5,
                        pageSizeOptions: [5, 10, 20, 50, 100],
                        emptyRowsWhenPaging: false,
                        showTitle: false,
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

export default QualitySummary;
