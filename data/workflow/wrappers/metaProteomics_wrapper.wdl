version 1.0
import "metapro_main.wdl" as metapro_main

workflow main_workflow {
    input {
        Array[Object] mapper_list
        String QVALUE_THRESHOLD
        File MASIC_PARAM_FILE_LOC
        File MSGFPLUS_PARAM_FILE_LOC
        File CONTAMINANT_FILE_LOC
        String STUDY
        String EXECUTION_RESOURCE
        String DATA_URL
        String OUTDIR
    }

    call metapro_main.metapro as metapro {
        input: 
            mapper_list=mapper_list,
            QVALUE_THRESHOLD=QVALUE_THRESHOLD,
            MASIC_PARAM_FILE_LOC=MASIC_PARAM_FILE_LOC,
            MSGFPLUS_PARAM_FILE_LOC=MSGFPLUS_PARAM_FILE_LOC,
            CONTAMINANT_FILE_LOC=CONTAMINANT_FILE_LOC,
            STUDY=STUDY,
            EXECUTION_RESOURCE=EXECUTION_RESOURCE,
            DATA_URL=DATA_URL,
            OUTDIR=OUTDIR
    }
}
