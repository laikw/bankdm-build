## Purpose
The purpose of this repo is to provide sample codes to illustrate MLOps with the data source coming from RedShift.
RedShift ML is also demostrated.


## Pre-req
SageMaker Studio to be created and attached to the VPC (not the default option). 
Create a SageMaker project for building, training and deployment. Instructions are at https://sagemaker-immersionday.workshop.aws/en/lab6.html
Overwrite the files from this repo.


## Flow of the demo
The notebook have been tested using 'Python 3 (Data Science)'.

1. Create the necessary IAM roles and policies. (Notebook 01)
2. Create secret in Secret Manager and RedShift cluster. (Notebook 01)
3. Explore the data (optional) (Notebook 02)
4. Copy the csv file to S3, create and load the csv data to Athena. (Notebook 03)
5. Create RedShift schema and table. Insert csv data to RedShift using Athena. (Notebook 03)


## Reference
Some codes were taken from the following sources and edited from there:
- https://github.com/data-science-on-aws/workshop
- https://github.com/aws-samples/amazon-sagemaker-immersion-day
- https://aws.amazon.com/blogs/aws/amazon-redshift-ml-is-now-generally-available-use-sql-to-create-machine-learning-models-and-make-predictions-from-your-data/
