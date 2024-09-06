import React, { useState, useEffect } from 'react';
import {
    Card, CardBody, Col, Row, Collapse,
} from 'reactstrap';

import { validFile } from '../../../../common/util';
import FileSelector from '../../../../common/FileSelector';
import { MyTooltip } from '../../../../common/MyTooltip';

import { initialMetaMAGs, workflowInputTips } from '../Defaults';
import { Header } from '../../../Common/Forms/CardHeader';

export function MetaMAGs(props) {

    const [form, setState] = useState({ ...initialMetaMAGs });
    const [collapseParms, setCollapseParms] = useState(false);
    const [doValidation, setDoValidation] = useState(0);

    const toggleParms = () => {
        setCollapseParms(!collapseParms);
    }

    const handleFileSelection = (filename, fieldname, index, key) => {
        // reset autofills when the sam_file changed
        // if (fieldname === 'sam_file') {
        //     Object.keys(form.metaAssemblyOutputFiles).forEach(file => {
        //         form[file] = '';
        //         form[file + '_validInput'] = false;
        //         form[file + '_autoFill'] = true;
        //         form[file + '_display'] = '';
        //     })
        // }
        // // reset autofills when the proteins_file changed
        // if (fieldname === 'proteins_file') {
        //     Object.keys(form.metaAnnotationOutputFiles).forEach(file => {
        //         form[file] = '';
        //         form[file + '_validInput'] = false;
        //         form[file + '_autoFill'] = true;
        //         form[file + '_display'] = '';
        //     })
        // }
        if (!validFile(key, filename)) {
            setState({
                ...form,
                [fieldname]: filename,
                [fieldname + '_validInput']: false,
                [fieldname + '_autoFill']: false,
                [fieldname + '_display']: key
            });
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        form[fieldname] = filename;
        form[fieldname + '_validInput'] = true;
        form[fieldname + '_autoFill'] = false;
        form[fieldname + '_display'] = key;

        const samEnd = '_sorted.bam';
        if (key.startsWith('projects/') && key.endsWith(samEnd)) {
            // auto fill inputs
            Object.keys(form.metaAssemblyOutputFiles).forEach(file => {
                form[file] = filename.replace(new RegExp('/\\w+' + samEnd + '$'), '/' + form.metaAssemblyOutputFiles[file]);
                form[file + '_validInput'] = true;
                form[file + '_autoFill'] = true;
                form[file + '_display'] = key.replace(new RegExp('/\\w+' + samEnd + '$'), '/' + form.metaAssemblyOutputFiles[file]);
            })

        }

        const proteinsEnd = '_proteins.faa';
        if (key.startsWith('projects/') && key.endsWith(proteinsEnd)) {
            // auto fill inputs
            Object.keys(form.metaAnnotationOutputFiles).forEach(file => {
                form[file] = filename.replace(new RegExp(proteinsEnd + '$'), form.metaAnnotationOutputFiles[file]);
                form[file + '_validInput'] = true;
                form[file + '_autoFill'] = true;
                form[file + '_display'] = key.replace(new RegExp(proteinsEnd + '$'), form.metaAnnotationOutputFiles[file]);
            })

        }
        setDoValidation(doValidation + 1);
    }

    const handleOptionalFileSelection = (filename, fieldname, index, key) => {
        if (key && !validFile(key, filename)) {
            setState({
                ...form,
                [fieldname + '_validInput']: false
            });
            form.validForm = false;
            props.setParams(form, props.full_name);
            return;
        }
        setState({
            ...form,
            [fieldname]: filename, [fieldname + '_validInput']: true, [fieldname + '_display']: key
        });
        setDoValidation(doValidation + 1);
    }

    //trigger validation method when input changes
    useEffect(() => {
        let errMessage = '';

        if (!form.contig_file_validInput) {
            errMessage += "Invalid contig input<br />";
        }
        if (!form.sam_file_validInput) {
            errMessage += "Invalid sam input<br />";
        }
        if (!form.gff_file_validInput) {
            errMessage += "Invalid gff input<br />";
        }
        if (!form.proteins_file_validInput) {
            errMessage += "Invalid proteins input<br />";
        }
        if (!form.cog_file_validInput) {
            errMessage += "Invalid cog input<br />";
        }
        if (!form.ec_file_validInput) {
            errMessage += "Invalid ec input<br />";
        }
        if (!form.ko_file_validInput) {
            errMessage += "Invalid ko input<br />";
        }
        if (!form.pfam_file_validInput) {
            errMessage += "Invalid pfam input<br />";
        }
        if (!form.tigrfam_file_validInput) {
            errMessage += "Invalid tigrfam input<br />";
        }
        if (!form.crispr_file_validInput) {
            errMessage += "Invalid crispr input<br />";
        }
        if (!form.product_names_file_validInput) {
            errMessage += "Invalid product_names input<br />";
        }
        if (!form.gene_phylogeny_file_validInput) {
            errMessage += "Invalid gene_phylogeny input<br />";
        }
        if (!form.lineage_file_validInput) {
            errMessage += "Invalid lineage input<br />";
        }
        if (!form.map_file_validInput) {
            errMessage += "Invalid map input<br />";
        }

        if (errMessage !== '') {
            form.validForm = false;
        } else {
            //errors only contains deleted dynamic input hidden errors
            form.validForm = true;
        }
        form.errMessage = errMessage;
        //force updating parent's inputParams
        props.setParams(form, props.full_name);
    }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Card className="workflow-card">
            <Header toggle={true} toggleParms={toggleParms} title={'Input'} collapseParms={collapseParms} />
            <Collapse isOpen={!collapseParms} id={"collapseParameters-" + props.name} >
                <CardBody>
                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-sam_file' text="sam/bam file" tooltip={workflowInputTips['MetaMAGs']['sam_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.sam_file_validInput}
                                dataSources={['project', 'upload', 'public', 'globus']}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Assembly']}
                                fileTypes={['sam', 'bam']} fieldname={'sam_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-contig_file' text="contig file" tooltip={workflowInputTips['MetaMAGs']['contig_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['contig_file'], key: form['contig_file_display'], autoFill: form['contig_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.contig_file_validInput}
                                dataSources={['project', 'upload', 'public', 'globus']}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Assembly']}
                                fileTypes={['fasta', 'fa', 'faa', 'fasta.gz', 'fa.gz', 'fna', 'fna.gz']}
                                fieldname={'contig_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-proteins_file' text="proteins file" tooltip={workflowInputTips['MetaMAGs']['proteins_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.proteins_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Pipeline', 'Metagenome Annotation']}
                                fileTypes={['faa']} fieldname={'proteins_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-gff_file' text="gff file" tooltip={workflowInputTips['MetaMAGs']['gff_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['gff_file'], key: form['gff_file_display'], autoFill: form['gff_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.gff_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['gff']} fieldname={'gff_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-cog_file' text="cog file" tooltip={workflowInputTips['MetaMAGs']['cog_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['cog_file'], key: form['cog_file_display'], autoFill: form['cog_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.cog_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['gff']} fieldname={'cog_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-ec_file' text="ec file" tooltip={workflowInputTips['MetaMAGs']['ec_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['ec_file'], key: form['ec_file_display'], autoFill: form['ec_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.ec_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv']} fieldname={'ec_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-ko_file' text="ko file" tooltip={workflowInputTips['MetaMAGs']['ko_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['ko_file'], key: form['ko_file_display'], autoFill: form['ko_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.ko_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv']} fieldname={'ko_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-pfam_file' text="pfam file" tooltip={workflowInputTips['MetaMAGs']['pfam_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['pfam_file'], key: form['pfam_file_display'], autoFill: form['pfam_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.pfam_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['gff']} fieldname={'pfam_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-tigrfam_file' text="tigrfam file" tooltip={workflowInputTips['MetaMAGs']['tigrfam_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['tigrfam_file'], key: form['tigrfam_file_display'], autoFill: form['tigrfam_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.tigrfam_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['gff']} fieldname={'tigrfam_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-crispr_file' text="crispr file" tooltip={workflowInputTips['MetaMAGs']['crispr_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['crispr_file'], key: form['crispr_file_display'], autoFill: form['crispr_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.crispr_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv','crisprs']} fieldname={'crispr_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-product_names_file' text="product_names file" tooltip={workflowInputTips['MetaMAGs']['product_names_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['product_names_file'], key: form['product_names_file_display'], autoFill: form['product_names_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.product_names_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv']} fieldname={'product_names_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-gene_phylogeny_file' text="gene_phylogeny file" tooltip={workflowInputTips['MetaMAGs']['gene_phylogeny_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['gene_phylogeny_file'], key: form['gene_phylogeny_file_display'], autoFill: form['gene_phylogeny_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.gene_phylogeny_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv']} fieldname={'gene_phylogeny_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-lineage_file' text="lineage file" tooltip={workflowInputTips['MetaMAGs']['lineage_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleFileSelection}
                                file={{ path: form['lineage_file'], key: form['lineage_file_display'], autoFill: form['lineage_file_autoFill'] }}
                                enableInput={true}
                                placeholder={'Select a file or enter a file http(s) url'}
                                validFile={form.lineage_file_validInput}
                                dataSources={['project', 'upload', 'public']}
                                projectTypes={['Metagenome Annotation']}
                                fileTypes={['tsv']} fieldname={'lineage_file'} viewFile={false} />
                        </Col>
                    </Row>
                    <br></br>

                    <Row>
                        <Col md="3">
                            <MyTooltip id='MetaMAGs-map_file' text="map file" tooltip={workflowInputTips['MetaMAGs']['map_file']} showTooltip={false} place="right" />
                        </Col>
                        <Col xs="12" md="9">
                            <FileSelector onChange={handleOptionalFileSelection}
                                enableInput={true}
                                placeholder={'(Optional) Select a file or enter a file http(s) url'}
                                validFile={form.map_file_validInput}
                                dataSources={['upload', 'public']}
                                fileTypes={['txt', 'tsv']} fieldname={'map_file'} viewFile={false}
                                isOptional={true} cleanupInput={true} />
                        </Col>
                    </Row>
                    <br></br>

                </CardBody>
            </Collapse>
        </Card>
    );
}