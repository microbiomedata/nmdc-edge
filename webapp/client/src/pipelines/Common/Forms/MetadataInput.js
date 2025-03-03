import React, { useEffect, useState } from 'react'
import { FaInfoCircle } from "react-icons/fa";
import {
  Row, Col, Input, ButtonGroup, Button
} from 'reactstrap';
import { useForm } from "react-hook-form";
import { getData } from '../../../common/util';
import MySelect from '../../../common/MySelect';
import { defaults, initialMetadata } from './Defaults';

const packageOptions = [
  { value: 'air', label: 'air' },
  { value: 'built environment', label: 'built environment' },
  { value: 'host-associated', label: 'host-associated' },
  { value: 'hydrocarbon resources-cores', label: 'hydrocarbon resources-cores' },
  { value: 'hydrocarbon resources-fluids_swabs', label: 'hydrocarbon resources-fluids_swabs' },
  { value: 'microbial mat_biofilm', label: 'microbial mat_biofilm' },
  { value: 'miscellaneous natural or artificial environment', label: 'miscellaneous natural or artificial environment' },
  { value: 'plant-associated', label: 'plant-associated' },
  { value: 'sediment', label: 'sediment' },
  { value: 'soil', label: 'soil' },
  { value: 'water', label: 'water' },
];

const MetadataInput = (props) => {
  const [submitting, setSubmitting] = useState(false);
  const [connect2nmdcserver, setConnect2nmdcserver] = useState(false);
  const [packageNames, setPackageNames] = useState([]);
  const [studyOptions, setStudyOptions] = useState([{ value: 'new', label: 'Create New Study' }, { value: 'test', label: 'Test Study' }]);
  const [study, setStudy] = useState('new');
  const [form, setState] = useState({ ...initialMetadata });
  const [doValidation, setDoValidation] = useState(0);
  const { register, trigger, clearErrors, setValue, formState: { errors } } = useForm({
    mode: defaults['form_mode'],
  });

  const studyNameReg = {
    ...register("study_name", {
      required: "Study name is required",
    })
  };

  const emailReg = {
    ...register("email", {
      required: 'Email is required',
      pattern: { // Validation pattern
        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i,
        message: 'Invalid email address'
      }
    })
  };

  const sampleNameReg = {
    ...register("sample_name", {
      required: "Sample name is required"
    })
  };

  const setNewState = (e) => {
    setState({
      ...form,
      [e.target.name]: e.target.value
    });
    setDoValidation(doValidation + 1);
  }

  const setNewState2 = (name, value) => {
    setState({
      ...form,
      [name]: value
    });
    setDoValidation(doValidation + 1);
  }

  //default 1 dataset
  useEffect(() => {
    setState({ ...initialMetadata });
    setDoValidation(doValidation + 1);
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    function getNmdcMetadataSubmissions() {
      let url = "/auth-api/user/project/getmetadatasubmissions";
      setSubmitting(true);
      getData(url)
        .then(data => {
          //console.log(data)
          setSubmitting(false);
          //generate submissionOptions
          let options = [
            { value: 'new', label: 'Create New Study' },
          ];
          const submissions = data.metadata_submissions;
          submissions.forEach((submission) => {
            options.push({ value: submission.id, label: submission.study_name });
          });
          setStudyOptions(options);
          setConnect2nmdcserver(true);
        })
        .catch(error => {
          setSubmitting(false);
        });
    }
    clearErrors();
    getNmdcMetadataSubmissions();
  }, []);// eslint-disable-line react-hooks/exhaustive-deps


  useEffect(() => {
    //validate form
    trigger().then(result => {
      form.validForm = result;
      if (result) {
        form.errMessage = '';
      } else if (!form.metadata) {
        form.errMessage = '';
        form.validForm = true;
      } else {
        let errMessage = '';
        if (study === 'new' && errors.study_name) {
          errMessage += errors.study_name.message + ". ";
        }
        if (study === 'new' && errors.email) {
          errMessage += errors.email.message + ". ";
        }
        if (errors.sample_name) {
          errMessage += errors.sample_name.message + ". ";
        }
        form.errMessage = errMessage;
        if (form.errMessage === '') {
          form.validForm = true;
        }
      }
      //force updating parent's inputParams
      props.setParams(form, props.type);
    });
  }, [doValidation]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Row>
        <Col md="3">Submit to NMDC Submission Portal &nbsp;<a href='https://data.microbiomedata.org/submission/home' target='_blank' rel="noreferrer"><FaInfoCircle /></a></Col>
        <Col xs="12" md="9">
          <ButtonGroup className="mr-3" aria-label="First group" size="sm">
            <Button color="outline-primary" onClick={() => {
              setNewState2("metadata", true)
            }}
              active={form.metadata}>Yes</Button>
            <Button color="outline-primary" onClick={() => {
              setNewState2("metadata", false)
            }}
              active={!form.metadata}>No</Button>
          </ButtonGroup>
        </Col>
      </Row>
      <br></br>
      {form.metadata && <>
        <Row>
          <Col md="3"> Create New or Select Existing Study  </Col>
          <Col xs="12" md="9">
            <MySelect
              name="study"
              defaultValue={studyOptions[0]}
              options={studyOptions}
              onChange={e => {
                setStudy(e.value);
                setNewState2('metadataSubmissionId', e.value);
              }}
              isClearable={false}
            />
          </Col>
        </Row>
        <br></br>
        {study === 'new' && <>
          <Row>
            <Col md="3">
              Study Name <a href='https://docs.microbiomedata.org/howto_guides/submit2nmdc#study' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
            </Col>
            <Col xs="12" md="9">
              <Input type="text" name="study_name" id="study_name" defaultValue={form.studyName}
                style={errors.study_name ? defaults.inputStyleWarning : defaults.inputStyle}
                onChange={(e) => {
                  studyNameReg.onChange(e); // method from hook form register
                  setNewState(e); // your method
                  setNewState2('studyName', e.target.value);
                }}
                innerRef={studyNameReg.ref}
              />
              {form.studyName && errors.study_name && <p className="edge-form-input-error">{errors.study_name.message}</p>}
            </Col>
          </Row>
          <br></br>
          <Row>
            <Col md="3">
              PI Email <a href='https://docs.microbiomedata.org/howto_guides/submit2nmdc#study' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
            </Col>
            <Col xs="12" md="9">
              <Input type="text" name="email" defaultValue={form.piEmail}
                style={errors.email ? defaults.inputStyleWarning : defaults.inputStyle}
                onChange={(e) => {
                  emailReg.onChange(e); // method from hook form register
                  setNewState2('piEmail', e.target.value); // your method
                }}
                innerRef={emailReg.ref}
              />
              {form.piEmail && errors.email && <p className="edge-form-input-error">{errors.email.message}</p>}
            </Col>
          </Row>
          <br></br>
          <Row>
            <Col md="3">
              Environmental Extensions <a href='https://docs.microbiomedata.org/howto_guides/submit2nmdc#environmental-extension' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
              <br></br>
              <span className="text-muted edge-text-size-small">
                (Choose environmental extensions for your data)
              </span>
            </Col>
            <Col xs="12" md="9">
              <MySelect
                name="packageNames"
                options={packageOptions}
                onChange={e => {
                  setPackageNames(e.map(item => item.value));
                  setNewState2('packageNames', e.map(item => item.value));
                }}
                isClearable={true}
                isMulti={true}
              />
            </Col>
          </Row>
          <br></br>
        </>}
        <Row>
          <Col md="3">
            Sample Name <a href='https://docs.microbiomedata.org/howto_guides/submit2nmdc#sample-metadata' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
          </Col>
          <Col xs="12" md="9">
            <Input type="text" name="sample_name" defaultValue={form.sampleName}
              style={errors.sample_name ? defaults.inputStyleWarning : defaults.inputStyle}
              onChange={(e) => {
                sampleNameReg.onChange(e); // method from hook form register
                setNewState2('sampleName', e.target.value);
              }}
              innerRef={sampleNameReg.ref}
            />
            {form.sampleName && errors.sample_name && <p className="edge-form-input-error">{errors.sample_name.message}</p>}
          </Col>
        </Row>
        <br></br>
      </>}
    </>
  )
}

export default MetadataInput;