import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme, handleTableNumberFilter } from '../../../../common/table';

function PlasmidSummary(props) {
    const [featureData, setFeatureData] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);
    
    const featureColumns = [
      {
          title: 'seq_name', field: 'seq_name',
      },
      {
          title: 'length', field: 'length', 
          customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['length']),
      },
      {
          title: 'topology', field: 'topology',
      },
      {
          title: 'n_genes', field: 'n_genes',
          customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['n_genes']),
      },
      {
          title: 'genetic_code', field: 'genetic_code',
      },
      {
          title: 'plasmid_score', field: 'plasmid_score',
          customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['plasmid_score']),
      },
      {
          title: 'fdr', field: 'fdr',
      },
      {
          title: 'n_hallmarks', field: 'n_hallmarks', 
          customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['n_hallmarks']),
      },
      {
          title: 'marker_enrichment', field: 'marker_enrichment',
          customFilterAndSearch: (term, rowData) => handleTableNumberFilter(term, rowData['marker_enrichment']),
      },
      {
          title: 'conjugation_genes', field: 'conjugation_genes', 
      },
      {
          title: 'amr_genes', field: 'amr_genes', 
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
                        exportFileName: 'plasmid',
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
                    //onRowClick={((evt, selectedRow) => setSelectedRow(selectedRow.tableData.id))}
                />
            </MuiThemeProvider>
            <br></br><br></br>
        </>

    );
}

export default PlasmidSummary;
