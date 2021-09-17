## Purpose
The purpose of this repo is to provide sample codes to illustrate MLOps with the data source coming from RedShift.
RedShift ML is also demostrated.


## Steps prior to running the notebooks
- Create a new VPC.
- SageMaker Studio to be created and attached to the VPC (not the default option). 
- Add IAM role to SageMaker role.
- Git clone this repo.
- Create a SageMaker project for building, training and deployment. Instructions are at https://sagemaker-immersionday.workshop.aws/en/lab6.html
- Overwrite the files from this repo to the modelbuild repo.

Detailed instructions are located at **instructions.md**

## Flow of the demo
The notebook have been tested using 'Python 3 (Data Science)'.

1. Create the necessary IAM roles and policies. (Notebook 01)
2. Create secret in Secret Manager and RedShift cluster. (Notebook 01)
3. Explore the data (optional) (Notebook 02)
4. Copy the csv file to S3, create and load the csv data to Athena. (Notebook 03)
5. Create RedShift schema and table. Insert csv data to RedShift using Athena. (Notebook 03)


## Roles
There are two roles used here - SageMaker Execution role and a role for executing things in RedShift (BankDemo role)

## Potential issue
- If the secret already exists and you are creating the RedShift cluster again in notebook 01, the secret will not be updated to the new password. Please update the password manually in Secrets Manager.
- The Security Group used for the RedShift and SageMaker Studio is the default one. If you are using another security group, please change the security_group_id in notebook 01.

## Clean up
Notebook 06 will clean up most of the resources created automatically. Other areas to delete manually are:
- SageMaker Studio
- S3 buckets
- VPC
- EFS used by SageMaker Studio
- Resources created by SageMaker Pipelines like CodePipeline, CodeBuild

## To-do
- Error handling

## Reference
Some codes were taken from the following sources and edited from there:
- https://github.com/data-science-on-aws/workshop
- https://github.com/aws-samples/amazon-sagemaker-immersion-day
- https://aws.amazon.com/blogs/aws/amazon-redshift-ml-is-now-generally-available-use-sql-to-create-machine-learning-models-and-make-predictions-from-your-data/
