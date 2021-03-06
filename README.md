## Purpose
The purpose of this repo is to provide sample codes to create a demo to illustrate MLOps (preprocessing, training, deploying etc) with the data source coming from RedShift. Other RedShift features like RedShift Spectrum, RedShift ML are also demostrated.

Disclaimer: The focus of this demo is to showcase the above and for simplicity, full IAM permissions are assigned. In production setting, best practices like least IAM permission should be used instead.  

## Services used
Below list the AWS services used in this demo:
- SageMaker
- Code* (Part of SageMaker Pipelines)
- RedShift
- S3
- Glue
- Athena
- Secrets Manager

## Prerequisite prior to running the notebooks
Before deploying the CloudFormation script, ensure the region that are you deploying to meets the following requirements:
- Able to create new VPC. i.e. the VPC limit is not reached
- SageMaker Studio has not been created in the region.

One workaround is to use a different region that supports SageMaker Studio.

Deploy the CloudFormation script `bankdm-cloudformation.yaml`. The script will do the following:
- Create a new VPC. 
- SageMaker Studio to be created and attached to the VPC (not the default option). Another way would be to allow connection from the Internet to RedShift which is not recommended. 
- Add IAM roles to SageMaker Execution role.

The following steps are to be done manually:
- Enable SageMaker jumpstart in SageMaker Studio
- Git clone this repo.
- Create a SageMaker project for building, training and deployment. 
- Overwrite the files from this repo to the modelbuild repo.

Detailed instructions are located in [**instructions.md**](instructions.md)

### High-level architecture diagram (after prerequistie steps)

The following diagram shows the high-level architecture diagram after completing the prerequisite steps. Do note that this is not the final architecture.

![diagram](img/diagram1.png)

To avoid any unexpected issues, a new VPC is created with one public subnet and one private subnet. The private subnet contains RedShift and VPC endpoints for SageMaker Studio and EFS storage. Later in the notebooks, the SageMaker Studio will access RedShift. With this architecture, all traffic will be within the VPC and RedShift does not need to be exposed to the Internet.

CodeCommit, CodeBuild, CodePipeline, and SageMaker Pipelines are used for MLOps and it is described later.

## High-level description of the demo
Note: Please complete the prerequisite steps above first.

### Notebook 01
- Create the necessary IAM roles and policies. 
- Create RedShift cluster, secret in Secret Manager and Lambda function. 

### Notebook 02 (optional)
- Explore the data.

### Notebook 03
- Copy the CSV file to S3. Create table in Glue Data Catalog (Glue table) and reference the CSV file.
- Use Athena to query the Glue table. 
- Create RedShift schema and external table referencing the Glue table.
- Create RedShift table. Insert CSV data to RedShift using Athena. 
- Manually save and commit the notebook in order to trigger the MLOps workflow.
- It takes ~12 minutes to run the pipeline and ~5 minutes to deploy the SageMaker endpoint.

### MLOps Workflow

The following diagram shows the MLOps workflow after manually committing the code:
![pipeline](img/pipeline1.png)

The diagrams below describe the workflow in more detail:
![pipeline](img/pipeline2.png)

![pipeline](img/pipeline3.png)

### High-level architecture diagram (after MLOps workflow executed successfully)

![diagram](img/diagram2.png)


### Notebook 04
- Once the SageMaker staging endpoint has been created, run predictions to the endpoint. 

### Notebook 05
- You can also use RedShift ML to create a model directly in RedShift using SQL statements. This leverages on SageMaker AutoPilot to create another model (different from the staging SageMaker endpoint). 
- Predictions can also be done directly in RedShift using SQL statements to the RedShift ML model. For this demo, SQL statements are provided in the notebook but you can also run the same in the RedShift query editer. 



## Roles
There are four roles used in this demo:
- SageMaker Execution role: For SageMaker Studio to create/access resources
- RedShift role (BankDM-RedShift): For RedShift cluster to access resources and for unloading data from RedShift to S3
- Lambda execution role (BankDM-Lambda): For Lambda function to access resources
- AmazonSageMakerServiceCatalogProductsUseRole (Default role): For SageMaker Pipelines to create/access resources


## Notes
- The notebooks do not store any variables. In other words, there is no transferring of variables between notebooks. 
- If the secret already exists and you are creating the RedShift cluster again in notebook 01, the secret will not be updated to the new password. Please update the password manually in Secrets Manager. This is to prevent accidential update of the secret when you rerun the notebook while the RedShift cluster is still running. 
- The Security Group used for the RedShift and SageMaker Studio is the default one. If you are using another security group, please change the security_group_id in notebook 01.
- If you change any names such as secret/role name, you may have to edit the SageMaker Pipelines code under 'pipelines/bankdm'.

## Clean up
Notebook06 does not delete VPC, SageMaker Studio, SageMaker Pipelines, CodePipelines, S3, EFS etc. You can delete the SageMaker project with the AWS CLI command `aws sagemaker delete-project --project-name X`. This will remove the MLOps components like CodePipeline. 

Before deleting the CloudFormation, the following components needs to be deleted manually:
- In SageMaker Studio, shutdown SageMaker Studio by going to `File` -> `Shutdown` -> `Shut down all`
- EFS

If the CloudFormation has issues deleting the VPC, you can do so manually. 


## Possible enhancement
- Error handling
- Feature store
- Cloudformation to create other resources


## References
Some codes were taken from the following sources and edited from there:
- https://github.com/data-science-on-aws/workshop
- https://github.com/aws-samples/amazon-sagemaker-immersion-day
- https://aws.amazon.com/blogs/aws/amazon-redshift-ml-is-now-generally-available-use-sql-to-create-machine-learning-models-and-make-predictions-from-your-data/
- https://github.com/aws/amazon-sagemaker-examples/tree/master/sagemaker-pipelines/tabular/lambda-step
- https://aws.amazon.com/blogs/big-data/using-the-amazon-redshift-data-api-to-interact-with-amazon-redshift-clusters/