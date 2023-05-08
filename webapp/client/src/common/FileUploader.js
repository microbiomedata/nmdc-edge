import React, { useState, useRef } from 'react';
import {
    Input, InputGroup, InputGroupAddon,
} from 'reactstrap';
import Fab from '@material-ui/core/Fab';
import ListIcon from '@material-ui/icons/List';
import {colors} from './Colors';

export const FileUploader = (props) => {
    const inputFile = useRef(null);
    const [input_file, setInput_file] = useState('');

    const onFileChange = (event) => {
        event.stopPropagation();
        event.preventDefault();
        var file = event.target.files[0];
        setInput_file(file.name);
        props.onChange(file);
    }

    const onOpenFileSelector = () => {
        // `current` points to the mounted file input element
        inputFile.current.click();
    };

    return (
        <>
            <InputGroup>
                <input type='file' accept={props.accept}
                    ref={inputFile} style={{ display: 'none' }} onChange={(e) => onFileChange(e)} />
                <Input style={{ borderRadius: '5px', backgroundColor: 'white' }} type="text" name="batch_input_excel" id="batch_input_excel"
                    placeholder="Upload a file"
                    value={input_file} disabled />
                <InputGroupAddon addonType="append">
                    <Fab size='small' style={{ marginLeft: 10, color: colors.primary, backgroundColor: 'white', }} >
                        <ListIcon onClick={() => onOpenFileSelector()} />
                    </Fab>
                </InputGroupAddon>
            </InputGroup>
        </>
    );
}

export default FileUploader;