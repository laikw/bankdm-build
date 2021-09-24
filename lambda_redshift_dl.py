# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from botocore.exceptions import WaiterError
from botocore.waiter import WaiterModel
from botocore.waiter import create_waiter_with_client
import boto3
import boto3.session

import json
import time
import os
import random
import datetime
import operator
import logging

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    
    secret_name='bankdm_redshift_login' ## replace the secret name with yours
    bucket = event['bucket']    
    prefix = 'bankdm'
    
    session = boto3.session.Session()
    region = session.region_name
    
    client_sts = boto3.client('sts')
    accountID = client_sts.get_caller_identity()["Account"]    
    logger.info("Account ID: %s", accountID)
    
    bc_session = s.get_session()
    
    session = boto3.Session(
            botocore_session=bc_session,
            region_name=region,
        )
    
    client = boto3.client('sagemaker')
    s3 = boto3.client('s3', region_name=region)
    
    # Create custom waiter for the Redshift Data API to wait for finish execution of current SQL statement
    waiter_name = 'DataAPIExecution'
    
    delay=2
    max_attempts=3
    
    #Configure the waiter settings
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
    
    
    # Need the actual IAM role
    redshift_iam_role = f'arn:aws:iam::{accountID}:role/BankDM-RedShift'
    
    # Below code is to get RedShift username and password from secrets manager
    secretsmanager = boto3.client('secretsmanager')
    
    try:
        get_secret_value_response = secretsmanager.get_secret_value(
                SecretId=secret_name
            )
        secret_arn=get_secret_value_response['ARN']

    except ClientError as e:
        print("Error retrieving secret. Error: " + e.response['Error']['Message'])

    else:
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    secret_json = json.loads(secret)
    master_user_name = secret_json['username']
    master_user_pw = secret_json['password']
    redshift_port = secret_json['port']
    redshift_cluster_identifier = secret_json['dbClusterIdentifier']
    redshift_endpoint_address = secret_json['host']

    database_name_redshift = secret_json['database_name_redshift']

    schema_redshift = secret_json['schema_redshift']

    table_name_redshift = secret_json['table_name_redshift']

    
    # Setup the client
    client_redshift = session.client("redshift-data")
    print("Data API client successfully loaded")
    
    waiter_model = WaiterModel(waiter_config)
    custom_waiter = create_waiter_with_client(waiter_name, waiter_model, client_redshift)
    
    redshift_unload_path = 's3://{}/{}/'.format(bucket,prefix) + 'unload/'
    logger.info("S3 filepath is %s" %redshift_unload_path)
    
    # Unload the data from RedShift to S3
    query_str = f"unload('select * from {schema_redshift}.{table_name_redshift};') to '{redshift_unload_path}' iam_role '{redshift_iam_role}' format as CSV header ALLOWOVERWRITE GZIP"
    print("Unloading string: " + query_str)
    
    res = client_redshift.execute_statement(Database= database_name_redshift, SecretArn= secret_arn, Sql= query_str, ClusterIdentifier= redshift_cluster_identifier)
    print("Redshift Data API execution started ...")
    id = res["Id"]
    
    # Reset the 'delay' attribute of the waiter to 20 seconds for the UNLOAD to finish.
    waiter_config["waiters"]["DataAPIExecution"]["delay"] = 20
    waiter_model = WaiterModel(waiter_config)
    custom_waiter = create_waiter_with_client(waiter_name, waiter_model, client_redshift)
    
    # Waiter in try block and wait for DATA API to return
    try:
        custom_waiter.wait(Id=id)
        print("Done waiting to finish Data API.")
    except WaiterError as e:
        print (e)
        
    print("Query execution complete")
    
    return {
        "statusCode": 200,
        "body": json.dumps("Done")
    }