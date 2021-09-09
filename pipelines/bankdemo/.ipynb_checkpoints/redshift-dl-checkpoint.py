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
import botocore.session as s
from botocore.exceptions import ClientError
import json
import boto3
import boto3.session
from boto3.session import Session

import time
import os
import random
import datetime
import operator
from botocore.exceptions import WaiterError
from botocore.waiter import WaiterModel
from botocore.waiter import create_waiter_with_client

import pandas as pd
import numpy as np

import argparse
import logging
import pathlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# Create custom waiter for the Redshift Data API to wait for finish execution of current SQL statement
waiter_name = 'DataAPIExecution'

delay=2
max_attempts=3

# Configure the waiter settings for RedShift Data API
waiter_config = {
  'version': 2,
  'waiters': {
    'DataAPIExecution': {
      'operation': 'DescribeStatement',
      'delay': delay,
      'maxAttempts': max_attempts,
      'acceptors': [
        {
          "matcher": "path",
          "expected": "FINISHED",
          "argument": "Status",
          "state": "success"
        },
        {
          "matcher": "pathAny",
          "expected": ["PICKED","STARTED","SUBMITTED"],
          "argument": "Status",
          "state": "retry"
        },
        {
          "matcher": "pathAny",
          "expected": ["FAILED","ABORTED"],
          "argument": "Status",
          "state": "failure"
        }
      ],
    },
  },
}

# Need this function to get the region
def detect_running_region():
    """Dynamically determine the region from a running Glue job (or anything on EC2 for
    that matter)."""
    easy_checks = [
        # check if set through ENV vars
        os.environ.get('AWS_REGION'),
        os.environ.get('AWS_DEFAULT_REGION'),
        # else check if set in config or in boto already
        boto3.DEFAULT_SESSION.region_name if boto3.DEFAULT_SESSION else None,
        boto3.Session().region_name,
    ]
    for region in easy_checks:
        if region:
            return region

    # else query an external service
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-identity-documents.html
    r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
    response_json = r.json()
    return response_json.get('region')

if __name__ == "__main__":
    logger.info("Starting redshift processing.")
    base_dir = "/opt/ml/processing"
    
    
    parser = argparse.ArgumentParser()
    # Input data is the S3 bucket
    parser.add_argument("--input-data", type=str, required=True)
    args = parser.parse_args()

    input_data = args.input_data
    logger.info("Input data: %s", input_data)
    s3_bucket = input_data
    
    client_sts = boto3.client('sts')
    logger.info(client_sts.get_caller_identity())
#     client = boto3.client("sts", aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    accountID = client_sts.get_caller_identity()["Account"]    
    logger.info("Account ID: %s", accountID)
    
    secret_name='bankdemo_redshift_login' ## replace the secret name with yours
    session = boto3.session.Session()
#     region = session.region_name # This returns null
    region = detect_running_region()
    logger.info("Region: %s", region)

    # S3 details for unloading data
    s3_prefix = 'bankdemo-unload'    # prefix used for all data stored within the bucket
    s3_output_path = "s3://{}/{}/output".format(s3_bucket, s3_prefix)
    logger.info(s3_output_path)
    
    # RedShift
    redshift_iam_role ='arn:aws:iam::{}:role/BankDemo'.format(accountID)
    redshift_unload_path = s3_output_path + '/preprocess/'
    

    # Have to switch role as the default role is 'arn:aws:sts::<Account>:assumed-role/AmazonSageMakerServiceCatalogProductsUseRole/SageMaker'
    # Call the assume_role method of the STSConnection object and pass the role ARN and a role session name.
    assumed_role_object=client_sts.assume_role(
        RoleArn=redshift_iam_role,
        RoleSessionName="SMAssumeExecutionRoleSession1"
    )
    
    # Switch to the new role
    session = Session(aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
                  aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
                  aws_session_token=assumed_role_object['Credentials']['SessionToken'],
                     region_name=region)

    
    # Get secret details
    client_secrets = session.client(
            service_name='secretsmanager',
            region_name=region
        )

    try:
        get_secret_value_response = client_secrets.get_secret_value(
                SecretId=secret_name
            )
        secret_arn=get_secret_value_response['ARN']

    except ClientError as e:
        logger.info("Error retrieving secret. Error: " + e.response['Error']['Message'])

    else:
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    secret_json = json.loads(secret)

    cluster_id=secret_json['dbClusterIdentifier']
    db=secret_json['db']
    logger.info("Cluster_id: " + cluster_id + "\nDB: " + db + "\nSecret ARN: " + secret_arn)
    

    # Setup the RedShift client
    client_redshift = session.client("redshift-data")
    logger.info("Data API client successfully loaded")
    
    waiter_model = WaiterModel(waiter_config)
    custom_waiter = create_waiter_with_client(waiter_name, waiter_model, client_redshift)
    
    
    # Unload from RedShift to S3
#     query_str = "unload('select * from redshift.data;') to '" + redshift_unload_path + "' iam_role '" + redshift_iam_role + "' format as CSV header ALLOWOVERWRITE GZIP"
    query_str = f"unload('select * from redshift.data;') to '{redshift_unload_path}' iam_role '{redshift_iam_role}' format as CSV header ALLOWOVERWRITE GZIP"
    logger.info("query string: " + query_str)
    
    res = client_redshift.execute_statement(Database=db, SecretArn=secret_arn, Sql=query_str, ClusterIdentifier=cluster_id)
    
    id = res["Id"]

    # Reset the 'delay' attribute of the waiter to 20 seconds for the UNLOAD to finish.
    waiter_config["waiters"]["DataAPIExecution"]["delay"] = 20
    waiter_model = WaiterModel(waiter_config)
    custom_waiter = create_waiter_with_client(waiter_name, waiter_model, client_redshift)

    logger.info("Redshift Data API execution  started ...")
    # Waiter in try block and wait for DATA API to return
    try:
        custom_waiter.wait(Id=id)
        logger.info("Done waiting to finish Data API.")
    except WaiterError as e:
        logger.info (e)

    logger.info("Query execution complete")
    
    # Connect to S3 to check the unloaded data
    s3 = boto3.client('s3', region_name=region)

    split = redshift_unload_path.split('/')
    bucket = split[2]
    prefix = '/'.join(split[3:])
    logger.info("S3 filepath is %s" %redshift_unload_path)

    # List out the files in the S3 directory. There may be multiple files inside
    datafiles = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    keys = []
    for obj in datafiles['Contents']:
        keys.append(obj['Key'])
    
    # new variable is to determine if header should be written. 
    # It should only be written for the first file
    new = 0
    
    for key in keys:
        logger.info("Processing file: " + key)
        a = s3.get_object(Bucket=bucket, Key=key)
        
        #obj is the file name
        obj = a['Body']
                
        df = pd.read_csv(obj, compression='gzip', sep = ',')
    
        if new == 0:
            # Save the file to local directory
            df.to_csv('{}/raw/raw.csv'.format(base_dir),
                            mode="w",index=False,header=True)
            new = 1
        else:
            df.to_csv('{}/raw/raw.csv'.format(base_dir),
                            mode="a",index=False,header=False)
        
