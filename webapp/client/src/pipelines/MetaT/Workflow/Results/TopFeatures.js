import React, { useEffect, useState } from 'react';
import MaterialTable from "material-table";
import { MuiThemeProvider } from '@material-ui/core';
import { tableIcons, theme } from '../../../../common/table';

function TopFeatures(props) {
    const [featureData, setFeatureData] = useState([]);
    const [selectedRow, setSelectedRow] = useState(null);
    
    const featureColumns = [
        {
            title: 'seqid', field: 'seqid',
        },
        {
            title: 'featuretype', field: 'featuretype', 
        },
        {
            title: 'start', field: 'start',
        },
        {
            title: 'end', field: 'end', 
        },
        {
            title: 'length', field: 'length',
        },
        {
            title: 'strand', field: 'strand',
        },
        {
            title: 'frame', field: 'frame',
        },
        {
            title: 'product', field: 'product',
        },
        {
            title: 'read_count', field: 'read_count', 
        },
        {
            title: 'rpkm', field: 'rpkm',
        },
        {
            title: 'id', field: 'id', hidden: true
        },
        {
            title: 'source', field: 'source', hidden: true
        },
        {
            title: 'extra', field: 'extra', hidden: true
        },
        {
            title: 'cog', field: 'Cog', hidden: true
        },
        {
            title: 'pfam', field: 'pfam', hidden: true
        },
        {
            title: 'ko', field: 'ko', hidden: true
        },
        {
            title: 'ec_number', field: 'ec_number', hidden: true
        },
    ];
    //componentDidMount()
    useEffect(() => {
        let features = props.result.top_features.map(obj => {
            //console.log(obj)
            let rObj = {};
            rObj['read_count'] = obj.read_count;
            rObj['rpkm'] = obj.rpkm;
            rObj['featuretype'] = obj.featuretype;
            rObj['seqid'] = obj.seqid;
            rObj['id'] = obj.id;
            rObj['source'] = obj.source;
            rObj['start'] = obj.start;
            rObj['end'] = obj.end;
            rObj['length'] = obj.length;
            rObj['strand'] = obj.strand;
            rObj['frame'] = obj.frame;
            rObj['product'] = obj.product;
            rObj['cog'] = obj.cog;
            rObj['pfam'] = obj.pfam;
            rObj['ko'] = obj.ko;
            rObj['ec_number'] = obj.ec_number;
            if (obj['extra']) {
                rObj['extra'] = obj['extra'].toString();
            }

            return rObj;
        });

        setFeatureData(features);

    }, [props.result]);

    return (
        <>
            <MuiThemeProvider theme={theme}>
                <MaterialTable
                    title="Top_features"
                    columns={featureColumns}
                    icons={tableIcons}
                    data={featureData}
                    options={{
                        exportButton: false,
                        exportFileName: 'metaT_top_features',
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

export default TopFeatures;
