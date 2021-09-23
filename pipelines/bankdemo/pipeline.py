# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Example workflow pipeline script for pipeline.
                                               . -RegisterModel
                                              .
    Process-> Train -> Evaluate -> Condition .
                                              .
                                               . -(stop)
Implements a get_pipeline(**kwargs) method.
"""

import os

import boto3
import sagemaker
import sagemaker.session

from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput
from sagemaker.processing import (
    ProcessingInput,
    ProcessingOutput,
    ScriptProcessor,
)
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.conditions import (
    ConditionLessThanOrEqualTo,
)
from sagemaker.workflow.condition_step import (
    ConditionStep,
    JsonGet,
)
from sagemaker.model_metrics import (
    MetricsSource,
    ModelMetrics,
)
from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import (
    ProcessingStep,
    TrainingStep,
)
from sagemaker.workflow.step_collections import RegisterModel

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def get_sagemaker_client(region):
     """Gets the sagemaker client.

        Args:
            region: the aws region to start the session
            default_bucket: the bucket to use for storing the artifacts

        Returns:
            `sagemaker.session.Session instance
        """
     boto_session = boto3.Session(region_name=region)
     sagemaker_client = boto_session.client("sagemaker")
     return sagemaker_client


def get_session(region, default_bucket):
    """Gets the sagemaker session based on the region.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        `sagemaker.session.Session instance
    """

    boto_session = boto3.Session(region_name=region)

    sagemaker_client = boto_session.client("sagemaker")
    runtime_client = boto_session.client("sagemaker-runtime")
    return sagemaker.session.Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
        default_bucket=default_bucket,
    )

def get_pipeline_custom_tags(new_tags, region, sagemaker_project_arn=None):
    try:
        sm_client = get_sagemaker_client(region)
        response = sm_client.list_tags(
            ResourceArn=sagemaker_project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags.append(project_tag)
    except Exception as e:
        print(f"Error getting project tags: {e}")
    return new_tags


def get_pipeline(
    region,
    sagemaker_project_arn=None,
    role=None,
    default_bucket=None,
    model_package_group_name="BankDemo-Group",  # Choose any name
    pipeline_name="BankDemo-Pipeline",  # You can find your pipeline name in the Studio UI (project -> Pipelines -> name)
    base_job_prefix="BankDemo-",  # Choose any name
):
    """Gets a SageMaker ML Pipeline instance working with on CustomerChurn data.
    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts
    Returns:
        an instance of a pipeline
    """
    sagemaker_session = get_session(region, default_bucket)
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    # Parameters for pipeline execution
    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount", default_value=1
    )
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType", default_value="ml.m5.2xlarge"
    )
    training_instance_type = ParameterString(
        name="TrainingInstanceType", default_value="ml.m5.xlarge"
    )
    model_approval_status = ParameterString(
        name="ModelApprovalStatus",
        default_value="Approved"
#         default_value="PendingManualApproval",  # ModelApprovalStatus can be set to a default of "Approved" if you don't want manual approval.
    )
    s3bucket = ParameterString(
        name="InputDataUrl",
        default_value=default_bucket,  # Change this to point to the s3 location of your raw input data.
    )

    #---
    # Processing step for feature engineering. Used for both RedShift download and preprocessing
    sklearn_processor = SKLearnProcessor(
        framework_version="0.23-1",
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/sklearn-preprocess",  # choose any name
        sagemaker_session=sagemaker_session,
        role=role,
    )
    
    step_redshift_download = ProcessingStep(
        name="Step-RedShift-Download",  # choose any name
        processor=sklearn_processor,
        code=os.path.join(BASE_DIR, "redshift-dl.py"),
        job_arguments=["--input-data", s3bucket],
        outputs=[
            ProcessingOutput(output_name="raw", source="/opt/ml/processing/raw"),
        ],
    )
    
    step_process = ProcessingStep(
        name="Step-PreProcess",  # choose any name
        processor=sklearn_processor,
        inputs=[
            ProcessingInput(
                source=step_redshift_download.properties.ProcessingOutputConfig.Outputs[
                    "raw"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/raw",
            ),
        ],
        outputs=[
            ProcessingOutput(output_name="train", source="/opt/ml/processing/train"),
            ProcessingOutput(output_name="validation", source="/opt/ml/processing/validation"),
            ProcessingOutput(output_name="test", source="/opt/ml/processing/test"),
        ],
        code=os.path.join(BASE_DIR, "preprocess.py"),
    )
    #---

    #---
    # Training step for generating model artifacts
    model_path = f"s3://{sagemaker_session.default_bucket()}/{base_job_prefix}/Train"
    image_uri = sagemaker.image_uris.retrieve(
        framework="xgboost",  # we are using the Sagemaker built in xgboost algorithm
        region=region,
        version="1.0-1",
        py_version="py3",
        instance_type=training_instance_type,
    )
    
    save_interval = 5 
    # https://sagemaker.readthedocs.io/en/stable/api/training/estimators.html#sagemaker.estimator.Estimator
    xgb_train = Estimator(
        image_uri=image_uri,
        instance_type=training_instance_type,
        instance_count=1,
        output_path=model_path,
        base_job_name=f"{base_job_prefix}/Train",
        sagemaker_session=sagemaker_session,
        role=role,

    )
    xgb_train.set_hyperparameters(
        # https://github.com/dmlc/xgboost/blob/master/doc/parameter.rst
        objective="reg:squarederror",
        num_round=50,
        max_depth=6, # default
        eta=0.3, # default
        gamma=0, # default
        min_child_weight=1, # default
        subsample=0.7,
        silent=0,
            
    )
    
    # Outputs model automatically
    step_train = TrainingStep(
        name="Step-Train",
        estimator=xgb_train,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "validation"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )
    #---

    #---
    # Processing step for evaluation
    script_eval = ScriptProcessor(
        image_uri=image_uri,
        command=["python3"],
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{base_job_prefix}/script-eval",
        sagemaker_session=sagemaker_session,
        role=role,
    )
    
    evaluation_report = PropertyFile(
        name="EvaluationReport",
        output_name="evaluation",
        path="evaluation.json",
    )
    
    step_eval = ProcessingStep(
        name="Step-Eval",
        processor=script_eval,
        # Takes in the model and test data
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs[
                    "test"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/test",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation", source="/opt/ml/processing/evaluation"
            ),
        ],
        code=os.path.join(BASE_DIR, "evaluate.py"),
        property_files=[evaluation_report],
        
    )
    #---
    

    #---
    # Metric data
    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="{}/evaluation.json".format(
                step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"][
                    "S3Uri"
                ]
            ),
            content_type="application/json",
        )
    )
    
    # Condition step for evaluating model quality and branching execution
    cond_lte = ConditionLessThanOrEqualTo(  # You can change the condition here
        left=JsonGet(
            step=step_eval,
            property_file=evaluation_report,
            json_path="regression_metrics.mse.value",  # This should follow the structure of your report_dict defined in the evaluate.py file.
        ),
        right=10.0,  # You can change the threshold here
    )
    #---

    #---
    # Register model step that will be conditionally executed
    step_register = RegisterModel(
        name="Step-RegisterModel",
        estimator=xgb_train,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=["ml.m5.large"],
        transform_instances=["ml.m5.large"],
        model_package_group_name=model_package_group_name,
        approval_status=model_approval_status,
        model_metrics=model_metrics,
    )
    
    # Register model step that will be conditionally executed
    step_cond = ConditionStep(
        name="Step-AccuracyCond",
        conditions=[cond_lte],
        if_steps=[step_register],
        else_steps=[],
    )
    #---
    
    # Pipeline instance
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            processing_instance_type,
            processing_instance_count,
            training_instance_type,
            model_approval_status,
            s3bucket,
        ],
#         steps=[step_redshift_download, step_process],
        steps=[step_redshift_download, step_process, step_train, step_eval, step_cond],
        sagemaker_session=sagemaker_session,
    )
    return pipeline

