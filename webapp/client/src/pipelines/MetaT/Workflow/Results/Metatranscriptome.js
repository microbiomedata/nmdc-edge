import React from 'react';
import ReadsQC from './ReadsQC';
import ReadMapping from './ReadMapping';
import Annotation from './Annotation';
import Assembly from './Assembly';

function Metatranscriptome(props) {
    return (
        <>
            {props.result['qa-stats'] &&
                <ReadsQC title={'ReadsQC Result'} result={props.result['qa-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {props.result['assembly-stats'] &&
                <Assembly title={'Assembly Result'} result={props.result['assembly-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {props.result['annotation-stats'] &&
                <Annotation title={'Annotation Result'} result={props.result['annotation-stats']} userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
            {(props.result['mapback-stats'] || props.result['metat_output-features']) &&
                <ReadMapping title={'Read Mapping Result'} mapback={props.result['mapback-stats']} features={props.result['metat_output-features']}userType={props.type} allExpand={props.allExpand} allClosed={props.allClosed} />
            }
        </>
    );
}

export default Metatranscriptome;
