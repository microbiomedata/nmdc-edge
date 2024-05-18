import React, { useState, useEffect } from 'react';
import MetaAnnotation from '../../Workflow/Results/MetaAnnotation';
import MetaAssembly from '../../Workflow/Results/MetaAssembly';
import MetaMAGs from '../../Workflow/Results/MetaMAGs';
import ReadbasedAnalysis from '../../Workflow/Results/ReadbasedAnalysis';
import ReadsQC from '../../Workflow/Results/ReadsQC';
import VirusPlasmid from '../../../Virus/Workflow/Results/VirusPlasmid';
import { workflowlist } from '../Defaults';

function MetaGPipeline(props) {
    const [runStats, setRunStats] = useState({});
    //get workflow status
    useEffect(() => {
        let stats = {};

        props.stats.stats.forEach((item, i) => {
            stats[item.Workflow] = item.Status;
        });
        setRunStats(stats);
    }, []);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <>
            {props.result.workflows.map((workflow, index) => {
                if (workflow.paramsOn && workflow.name === 'ReadsQC' && runStats['ReadsQC'] === 'Done') {
                    return <ReadsQC key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                } else if (workflow.paramsOn && workflow.name === 'ReadbasedAnalysis' && runStats['Read-based Taxonomy Classification'] === 'Done') {
                    return <ReadbasedAnalysis key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                } else if (workflow.paramsOn && workflow.name === 'MetaAssembly' && runStats['Metagenome Assembly'] === 'Done') {
                    return <MetaAssembly key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                } else if (workflow.paramsOn && workflow.name === 'virus_plasmid' && runStats['Viruses and Plasmids'] === 'Done') {
                    return <VirusPlasmid key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                }else if (workflow.paramsOn && workflow.name === 'MetaAnnotation' && runStats['Metagenome Annotation'] === 'Done') {
                    return <MetaAnnotation key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                } else if (workflow.paramsOn && workflow.name === 'MetaMAGs' && runStats['Metagenome MAGs'] === 'Done') {
                    return <MetaMAGs key={index} result={props.result[workflow.name]} project={props.project} title={workflowlist[workflow.name].title + ' Result'} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
                } else {
                    return <></>;
                }
            })
            }
        </>
    );
}

export default MetaGPipeline;
