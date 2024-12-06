import React, { useState, useEffect } from 'react';
import {
  Col, Row, Input
} from 'reactstrap';
import { MyTooltip } from '../../../common/MyTooltip';
import { initialFileUpload } from './Defaults';

export function FileUpload(props) {
  const [
    form,
    setState
  ] = useState({ ...initialFileUpload });
  const [doValidation, setDoValidation] = useState(0);

  useEffect(() => {
    //validate form
    if (form.file || props.isOptional) {
      form.errMessage = '';
      form.validForm = true;
    } else {
      form.errMessage = 'File is required.';
      form.validForm = false;
    }
    //force updating parent's inputParams
    props.setParams(form, props.name);
  }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Row>
        <Col md="3">
          <MyTooltip id='fileupload' text={props.text ? props.text : "Upload File"} tooltip={initialFileUpload.upload_tip} showTooltip={true} place="right" />
        </Col>
        <Col xs="12" md="9">
          <Input
            type="file"
            id="file"
            onChange={(event) => {
              form['file'] = event.target.files[0];
              setDoValidation(doValidation + 1);
            }}
            accept={props.accept? props.accept: '*'}
          />
        </Col>
      </Row>
    </>
  );
}