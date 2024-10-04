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
  const [packageName, setPackageName] = useState(packageOptions[0].value);
  const [studyOptions, setStudyOptions] = useState([{ value: 'new', label: 'New Study' }]);
  const [study, setStudy] = useState('new');

  const { register, handleSubmit, formState: { errors }, clearErrors } = useForm({
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

  //submit button clicked
  const onSubmit = (data) => {
    const userData = {
      studyName: data.study_name,
      piEmail: data.email,
      packageName: packageName, 
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
            { value: 'new', label: 'New Study' },
          ];
          const submissions = data.metadata_submissions;
          submissions.forEach((submission) => {
            options.push({ value: submission.metadata_submission.id, label: submission.metadata_submission.study_name });
          });
          setStudyOptions(options);
        })
        .catch(error => {
          setSubmitting(false);
          alert(error);
        });
    }
    clearErrors();
    getNmdcMetadataSubmissions();
  }, []);// eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Modal isOpen={props.isOpen} centered>
      <LoaderDialog loading={submitting === true} text="Submitting..." />
      <Form onSubmit={handleSubmit(onSubmit)}>
        <ModalHeader className="justify-content-center">
          Study Information{/* 
          <br></br>
          <span className="pt-3 edge-text-size-small">
            (Note: all fields are required)
          </span> */}
        </ModalHeader>
        <ModalBody>
          <MySelect
            name="study"
            defaultValue={studyOptions[0]}
            options={studyOptions}
            onChange={e => {
              setStudy(e.value);
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
            <MySelect
              name="packageName"
              defaultValue={packageOptions[0]}
              options={packageOptions}
              onChange={e => {
                setPackageName(e.value);
              }}
              isClearable={false}
            />
            <br></br>
          </>}
        </ModalBody>
        <ModalFooter className="justify-content-center">
          <Button color="primary" type="submit">Submit</Button>{' '}
          <Button color="secondary" onClick={props.handleClickClose}>
            Cancel
          </Button>
        </ModalFooter>
      </Form>
    </Modal >
  )
}

export default MetadataSubmisssion;