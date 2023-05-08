import React from 'react';
import { Button, Modal, ModalHeader, ModalBody, ModalFooter } from 'reactstrap';
import Loader from 'react-loader-spinner';
import ReactJson from 'react-json-view'
import "react-loader-spinner/dist/loader/css/react-spinner-loader.css";
import FileBrowser from 'react-keyed-file-browser';
import 'react-keyed-file-browser/dist/react-keyed-file-browser.css';
import { colors } from './Colors';
import startCase from 'lodash.startcase';
import parse from 'html-react-parser';
import {FcFolder, FcOpenedFolder} from 'react-icons/fc';

export function ConfirmDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered>
            <ModalHeader >{props.title}</ModalHeader>
            <ModalBody>
                {props.message}
            </ModalBody>
            <ModalFooter>
                <Button color="primary" onClick={props.handleClickYes}>{startCase(props.action)}</Button>{' '}
                <Button color="secondary" onClick={props.handleClickClose} >Cancel</Button>
            </ModalFooter>
        </Modal>
    );
}

export function ConfirmDialogNoHeader(props) {
    return (
        <Modal isOpen={props.isOpen} centered>
            <ModalBody>
                {props.html ? parse(props.message) : props.message}
            </ModalBody>
            <ModalFooter className="justify-content-center">
                <Button color="primary" onClick={props.handleClickYes}>{startCase(props.action)}</Button>{' '}
                <Button color="secondary" onClick={props.handleClickClose} >Cancel</Button>
            </ModalFooter>
        </Modal>
    );
}
export function MessageDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered className={props.className ? props.className : 'modal-success'}>
            <ModalHeader toggle={props.handleClickClose}>{props.title ? props.title : 'Message'}</ModalHeader>
            <ModalBody>
                {props.html ? parse(props.message) : props.message}
            </ModalBody>
        </Modal>
    );
}

export function LoaderDialog(props) {
    return (
        <Modal isOpen={props.loading ? true : false} className="edge-loader">
            <div className="edge-loader justify-content-center white-text">
                <Loader type="Circles" color={colors.primary} height={100} width={100} />
                {props.text}
            </div>
        </Modal>
    );
}

export function FileBrowserDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered toggle={props.toggle} className={'modal-lg ' + props.className}>
            <ModalHeader toggle={props.toggle}>{props.title}</ModalHeader>
            <ModalBody className="edge-modal-body">
                <FileBrowser
                    files={props.files}
                    icons={{
                        Folder: <FcFolder className={'edge-fab-file-selector-icon'} />,
                        FolderOpen: <FcOpenedFolder className={'edge-fab-file-selector-icon'} />
                    }}
                    showActionBar={false}
                    onSelectFile={props.handleSelectedFile}
                    noFilesMessage={props.noFilesMessage}
                />
            </ModalBody>
        </Modal>
    );
}

export function FileViewerDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered toggle={props.toggle} className={'modal-lg ' + props.className}>
            <ModalHeader toggle={props.toggle}>{props.title}</ModalHeader>
            <ModalBody className="edge-modal-body">
                {(!props.type || props.type === 'json') &&
                    <ReactJson src={props.src} enableClipboard={false} displayDataTypes={false} />
                }
                {props.type === 'text' &&
                    <div className="edge-display-linebreak edge-component-center">
                        <textarea name="textarea-input" id="textarea-input" cols={100} rows={20}
                            value={props.src} onChange={(e) => {}} />
                    </div>
                }
            </ModalBody>
        </Modal>
    );
}

export function ImgDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered toggle={props.toggle} className={'modal-lg'} >
            <ModalHeader toggle={props.handleClickClose}>{props.title}</ModalHeader>
            <ModalBody >
                <img alt={""} src={props.img} width={'100%'} height={'100%'} />
            </ModalBody>
        </Modal>
    );
}

export function VideoDialog(props) {
    return (
        <Modal isOpen={props.isOpen} centered className={'modal-xl'} >
            <ModalHeader toggle={props.handleClickClose}>{props.title}</ModalHeader>
            <ModalBody >
                <video src={props.video} width="100%" height="100%" controls />
            </ModalBody>
        </Modal>
    );
}
