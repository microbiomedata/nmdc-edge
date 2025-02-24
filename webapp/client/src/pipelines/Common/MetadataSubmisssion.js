import React, { useEffect, useState } from 'react'
import { FaInfoCircle } from "react-icons/fa";
import { LoaderDialog } from '../../common/Dialogs';
import { getData } from '../../common/util';
import MySelect from '../../common/MySelect';
import {
  Button, Modal, ModalHeader, ModalBody, ModalFooter, Form, Input,
} from 'reactstrap';

import { useForm } from "react-hook-form";

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

const MetadataSubmisssion = (props) => {
  const [submitting, setSubmitting] = useState(false);
  const [packageNames, setPackageNames] = useState([]);
  const [studyOptions, setStudyOptions] = useState([{ value: 'new', label: 'Create New Study' },{ value: 'test', label: 'test Study' }]);
  const [study, setStudy] = useState('new');

  const { register, trigger, handleSubmit, formState: { errors }, clearErrors } = useForm({
    mode: 'onChange',
  });

  const studyNameReg = {
    ...register("study_name", {
      required: "Study name is required"
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

  //submit button clicked
  const onSubmit = (data) => {
    const userData = {
      studyName: data.study_name,
      piEmail: data.email,
      sampleName: data.sample_name,
      packageNames: packageNames,
      metadataSubmissionId: study
    };
    props.handleSuccess(userData);
  }

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
        })
        .catch(error => {
          setSubmitting(false);
          alert(error);
        });
    }
    clearErrors();
    setPackageNames([]);
    setStudy('new');
    if (props.connect2nmdcserver) {
      getNmdcMetadataSubmissions();
    }
  }, [props]);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Modal isOpen={props.isOpen} centered>
      <LoaderDialog loading={submitting === true} text="Submitting..." />
      <Form onSubmit={handleSubmit(onSubmit)}>
        <ModalHeader className="justify-content-center">
          Metadata Submission{/* 
          <br></br>
          <span className="pt-3 edge-text-size-small">
            (Note: all fields are required)
          </span> */}
        </ModalHeader>
        <ModalBody>
          Create New or Select Existing Study
          <MySelect
            name="study"
            defaultValue={studyOptions[0]}
            options={studyOptions}
            onChange={e => {
              setStudy(e.value);
              trigger("sample_name")
            }}
            isClearable={false}
          />
          <br></br>
          {study === 'new' && <>
            Study Name <a href='https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html#study' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
            <Input type="text" name="study_name" id="study_name" defaultValue={''}
              onChange={(e) => {
                studyNameReg.onChange(e); // method from hook form register
              }}
              innerRef={studyNameReg.ref}
            />
            {errors.study_name && <p className="edge-form-input-error">{errors.study_name.message}</p>}
            <br></br>

            PI Email <a href='https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html#study' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
            <Input type="text" name="email"
              onChange={(e) => {
                emailReg.onChange(e); // method from hook form register
              }}
              innerRef={emailReg.ref}
            />
            {errors.email && <p className="edge-form-input-error">{errors.email.message}</p>}
            <br></br>

            Environmental Package <a href='https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html#environmental-package' target='_blank' rel="noreferrer"><FaInfoCircle /></a>
            <br></br>
            <span className="text-muted edge-text-size-small">
              (Select the environmental packages that you collected samples from.)
            </span>
            <MySelect
              name="packageName"
              options={packageOptions}
              onChange={e => {
                setPackageNames(e.map(item => item.value));
              }}
              isClearable={true}
              isMulti={true}
            />
            <br></br>
          </>}
          Sample Name <a href='https://docs.microbiomedata.org/howto_guides/submit2nmdc#sample-metadata' target='_blank' rel="noreferrer"><FaInfoCircle /></a>

          <Input type="text" name="sample_name"
            onChange={(e) => {
              sampleNameReg.onChange(e); // method from hook form register
            }}
            innerRef={sampleNameReg.ref}
          />
          {errors.sample_name && <p className="edge-form-input-error">{errors.sample_name.message}</p>}

          <br></br>
        </ModalBody>
        <ModalFooter className="justify-content-center">
          <Button color="primary" type="submit" disabled={Object.keys(errors).length !== 0 || (study === 'new' && packageNames.length === 0)}>Submit</Button>{' '}
          <Button color="secondary" onClick={props.handleClickClose}>
            Cancel
          </Button>
        </ModalFooter>
      </Form>
    </Modal >
  )
}

export default MetadataSubmisssion;