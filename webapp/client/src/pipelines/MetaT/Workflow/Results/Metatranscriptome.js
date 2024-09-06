import React from 'react';
import ReadsQC from './ReadsQC';
import ReadMapping from './ReadMapping';
import Annotation from './Annotation';
import Assembly from './Assembly';

function Metatranscriptome(props) {
    return (
        <>
            {props.result['readsQC-stats'] &&
                <ReadsQC title={'ReadsQC Result'} result={props.result['readsQC-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {props.result['assembly-stats'] &&
                <Assembly title={'Assembly Result'} result={props.result['assembly-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {props.result['annotation-stats'] &&
                <Annotation title={'Annotation Result'} result={props.result['annotation-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {props.result['readMapping-features'] &&
                <ReadMapping title={'Read Mapping Result'} project={props.project} tooLarge={props.result['readMapping-features-too-large']} features={props.result['readMapping-features']} topFeatures={props.result['readMapping-top_features']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
        </>
    );
}

export default Metatranscriptome;
