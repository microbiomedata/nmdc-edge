import React, { useState, useEffect } from 'react';
import {
  Card, CardBody, Col, Row, Collapse, Input
} from 'reactstrap';
import { useForm } from "react-hook-form";
import { MyTooltip } from '../../../../common/MyTooltip';
import { Header } from '../../../Common/Forms/CardHeader';
import { defaults, initialSra2fastq, workflowInputTips } from '../Defaults';

export function Sra2fastq(props) {
  const [collapseParms, setCollapseParms] = useState(false);
  const { register, setValue, formState: { errors }, trigger } = useForm({
    mode: defaults['form_mode'],
  });


  const toggleParms = () => {
    setCollapseParms(!collapseParms);
  }
  const isValidAccessions = (accessions) => {
    if (!accessions) {
      if (props.required) {
        return false;
      } else {
        return true;
      }
    }
    const parts = accessions.split(",");
    for (var i = 0; i < parts.length; i++) {
      //if(!/^[a-zA-Z]{3}[0-9]{6,9}$/.test(parts[i].trim())) {
      if (!/^(srp|erp|drp|srx|erx|drx|srs|ers|drs|srr|err|drr|sra|era|dra)[0-9]{6,9}$/i.test(parts[i].trim())) {
        return false;
      }
    }
    return true;
  };

  const accessionReg = {
    ...register("accessions", {
      required: 'SRA accession(s) required.',
      validate: { // Validation pattern
        validAcession: (value) => isValidAccessions(value) || 'Invalid SRA accession(s) input.',
      }
    })
  };

  const [
    form,
    setState
  ] = useState(initialSra2fastq);
  const [doValidation, setDoValidation] = useState(0);

  const setNewState = (e) => {
    setState({
      ...form,
      [e.target.name]: e.target.value
    });
    setDoValidation(doValidation + 1);
  }

  useEffect(() => {
    setState({ ...initialSra2fastq });
    setValue('accessions', '', { shouldValidate: true });
    setDoValidation(doValidation + 1);
  }, [props.reset]);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    //validate form
    trigger().then(result => {
      form.validForm = result;
      if (result) {
        form.errMessage = '';
      } else {
        let errMessage = '';
        if (errors.accessions) {
          errMessage += errors.accessions.message;
        }
        form.errMessage = errMessage;
      }
      //force updating parent's inputParams
      props.setParams(form, props.full_name);
    });
  }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Row>
      <Col md="3">
        <MyTooltip id='accessionsTooltip' tooltip={workflowInputTips['sra2fastq']['accessions']}
          text='SRA Accession(s)' place={defaults.tooltipPlace} showTooltip={defaults.showTooltip} />

      </Col>
      <Col xs="12" md="9">

        <Input type="text" name="accessions" id="accessions" defaultValue={form.accessions}
          placeholder="ex: SRR1553609,SRX7852919"
          style={(errors.accessions) ? defaults.inputStyleWarning : defaults.inputStyle}
          onChange={(e) => {
            accessionReg.onChange(e); // method from hook form register
            setNewState(e); // your method
          }}
          innerRef={accessionReg.ref}
        />
        {errors && errors.accessions && <p className="edge-form-input-error">{errors.accessions.message}</p>}
      </Col>
    </Row>
  );
}
