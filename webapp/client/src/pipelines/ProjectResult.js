import React, { useEffect, useState } from 'react';
import { Col, Row, Button } from 'reactstrap';
import { LoaderDialog, FileViewerDialog } from '../common/Dialogs';
import { postData, fetchFile } from '../common/util';
import ProjectGeneral from './Common/Results/ProjectGeneral';
import ProjectOutputs from './Common/Results/ProjectOutputs';
import MetaAnnotation from './MetaG/Workflow/Results/MetaAnnotation';
import MetaAssembly from './MetaG/Workflow/Results/MetaAssembly';
import MetaMAGs from './MetaG/Workflow/Results/MetaMAGs';
import ReadbasedAnalysis from './MetaG/Workflow/Results/ReadbasedAnalysis';
import ReadsQC from './MetaG/Workflow/Results/ReadsQC';
import MetaGPipeline from './MetaG/Pipeline/Results/MetaGPipeline';
import Metatranscriptome from './MetaT/Workflow/Results/Metatranscriptome';
import EnviroMS from './OrganicM/Workflow/Results/EnviroMS';
import VirusPlasmid from './Virus/Workflow/Results/VirusPlasmid';
import Metaproteomics from './MetaP/Workflow/Results/Metaproteomics';

function ProjectResult(props) {
    const [project, setProject] = useState();
    const [type, setType] = useState();
    const [runStats, setRunStats] = useState();
    const [conf, setConf] = useState();
    const [result, setResult] = useState();
    const [outputs, setOutputs] = useState();
    const [loading, setLoading] = useState(false);
    const [error] = useState();
    const [view_log_file, setView_log_file] = useState(false);
    const [log_file_content, setLog_file_content] = useState('');
    const [allExpand, setAllExpand] = useState(0);
    const [allClosed, setAllClosed] = useState(0);
    //disable the expand | close
    const disableExpandClose = false;

    useEffect(() => {
        setProject(props.project);
        setType(props.type);
    }, [props.project, props.type]);

    useEffect(() => {
        function getProjectConf() {
            let projData = {
                code: project.code,
            };
            let url = "/api/project/conf";
            if (type === 'admin') {
                url = "/auth-api/admin/project/conf";
            }
            else if (type === 'user') {
                url = "/auth-api/user/project/conf";
            }
            postData(url, projData)
                .then(data => {
                    //console.log(data)
                    setConf(data);
                })
                .catch(error => {
                    alert(error);
                });
        }
        function getProjectRunStats() {
            let projData = {
                code: project.code,
            };
            let url = "/api/project/runstats";
            if (type === 'admin') {
                url = "/auth-api/admin/project/runstats";
            }
            else if (type === 'user') {
                url = "/auth-api/user/project/runstats";
            }
            postData(url, projData)
                .then(data => {
                    //console.log(data)
                    setRunStats(data);
                })
                .catch(error => {
                    alert(error);
                });
        }
        function getProjectResult() {
            let projData = {
                code: project.code,
            };
            let url = "/api/project/result";
            if (type === 'admin') {
                url = "/auth-api/admin/project/result";
            }
            else if (type === 'user') {
                url = "/auth-api/user/project/result";
            }
            postData(url, projData)
                .then(data => {
                    //console.log(data.result)
                    setResult(data.result);
                    setLoading(false);
                })
                .catch(error => {
                    alert(error);
                    setLoading(false);
                });
        }
        function isSummaryFile(value) {
            return /^\/virus_plasmid\/(.*)_summary\//.test(value.key) || /^\/virus_plasmid\/checkv\//.test(value.key);
        }
        function getProjectOutputs() {
            const userData = {
                code: project.code,
            };

            let url = "/api/project/outputs";
            if (type === 'admin') {
                url = "/auth-api/admin/project/outputs";
            }
            else if (type === 'user') {
                url = "/auth-api/user/project/outputs";
            }
            //project files
            postData(url, userData)
                .then(data => {
                    //console.log(data.fileData)
                    if (project.type === 'Viruses and Plasmids') {
                        data.fileData = data.fileData.filter(isSummaryFile);
                    }
                    setOutputs(data.fileData);
                }).catch(error => {
                    alert(error);
                });
        }

        if (project && project.code) {
            setLoading(true);
            getProjectConf();
            getProjectRunStats();
            if (project.status === 'complete' || (project.type === 'Metagenome Pipeline' && project.status === 'failed')) {
                getProjectResult();
                getProjectOutputs();
            }

        }
    }, [project, type]);

    function viewLogFile() {
        let url = "/projects/" + project.code + "/log.txt";
        fetchFile(url)
            .then(data => {
                setLog_file_content(data);
                setView_log_file(true);
            })
            .catch((error) => {
                alert(error);
            });;
    }

    function submit2nmdc() {
        console.log('submit2nmdc');
        
    }

    function onLogChange(data) {
        setLog_file_content(data);
    }

    return (
        <div className="animated fadeIn">
            <LoaderDialog loading={loading === true} text="Loading..." />
            <FileViewerDialog type={'text'} isOpen={view_log_file} toggle={e => setView_log_file(!view_log_file)} title={'log.txt'}
                src={log_file_content} onChange={onLogChange} />

            {error ?
                <Row className="justify-content-center">
                    <Col xs="12" md="10">
                        <div className="clearfix">
                            <p className="text-muted float-left">
                                The project might be deleted or you have no permission to access it.
                            </p>
                        </div>
                    </Col>
                </Row>
                :
                <>
                    {(project && project.status === 'failed' && props.type !== 'public') &&
                        <>
                            <Row className="justify-content-center">
                                <Col xs="12" md="10">
                                    <Button type="button" size="sm" color="primary" onClick={viewLogFile} >View Log</Button>
                                </Col>
                            </Row>
                            <br></br>
                        </>
                    }
                    {(project && project.status === 'complete' && props.type === 'user') &&
                        <>
                            <Row className="justify-content-center">
                                <Col xs="12" md="10">
                                    <Button type="button" size="sm" color="primary" onClick={submit2nmdc} >Submit to NMDC</Button>
                                </Col>
                            </Row>
                            <br></br>
                        </>
                    }
                    {(outputs || result) && !disableExpandClose &&
                        <Row className="justify-content-center">
                            <Col xs="12" md="10">
                                <p className="float-right">
                                    <Button size="sm" className="btn-pill" color="ghost-primary" onClick={() => setAllExpand(allExpand + 1)} > expand </Button>|
                                    <Button size="sm" className="btn-pill" color="ghost-primary" onClick={() => setAllClosed(allClosed + 1)} > close </Button>
                                    sections
                                </p>
                            </Col>
                        </Row>
                    }
                    <Row className="justify-content-center">
                        <Col xs="12" md="10">
                            <ProjectGeneral stats={runStats} conf={conf} project={project} title={'General'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                        </Col>
                    </Row>
                    {result &&
                        <Row className="justify-content-center">
                            <Col xs="12" md="10">
                                {project.type === 'ReadsQC' &&
                                    <ReadsQC result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Read-based Taxonomy Classification' &&
                                    <ReadbasedAnalysis result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metagenome Assembly' &&
                                    <MetaAssembly result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metagenome Annotation' &&
                                    <MetaAnnotation result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metagenome MAGs' &&
                                    <MetaMAGs result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metagenome Pipeline' && runStats &&
                                    <MetaGPipeline result={result} stats={runStats} project={project} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metatranscriptomics' &&
                                    <Metatranscriptome result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Natural Organic Matter' &&
                                    <EnviroMS result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Viruses and Plasmids' &&
                                    <VirusPlasmid result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                                {project.type === 'Metaproteomics' &&
                                    <Metaproteomics result={result} project={project} title={props.project.type + ' Result'} userType={type} allExpand={allExpand} allClosed={allClosed} />
                                }
                            </Col>
                        </Row>
                    }
                    {outputs &&
                        <Row className="justify-content-center">
                            <Col xs="12" md="10">
                                <ProjectOutputs outputs={outputs} filePath={"/projects/" + project.code + "/output"} allExpand={allExpand} allClosed={allClosed} />
                                {project.type === 'Viruses and Plasmids' &&
                                    <a href={'https://portal.nersc.gov/genomad/index.html'} target='_blank' rel='noreferrer'>{'Learn more about the Viruses and Plasmids outputs ...'}</a>
                                }
                            </Col>
                        </Row>
                    }
                    <br></br>
                    <br></br>
                </>
            }
        </div >
    );
}

export default ProjectResult;
