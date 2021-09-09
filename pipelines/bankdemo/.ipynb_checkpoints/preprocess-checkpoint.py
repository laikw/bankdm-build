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
import argparse
import logging
import pathlib

import boto3
import numpy as np
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    logger.info("Starting preprocessing.")
    base_dir = "/opt/ml/processing"

    # Specify the location of file that was produced by previous step
    fn = '/opt/ml/processing/raw/raw.csv'
    logger.info("Reading downloaded data.")

    # read in csv
    data = pd.read_csv(fn, low_memory=False)

    data['no_previous_contact'] = np.where(data['pdays'] == 999, 1, 0)                                 # Indicator variable to capture when pdays takes a value of 999
    data['not_working'] = np.where(np.in1d(data['job'], ['student', 'retired', 'unemployed']), 1, 0)   # Indicator for individuals not actively employed
    model_data = pd.get_dummies(data)                                                                  # Convert categorical variables to sets of indicators
    
    model_data = model_data.drop(['duration', 'emp_var_rate', 'cons_price_idx', 'cons_conf_idx', 'euribor3m', 'nr_employed'], axis=1)
    
    train_data, validation_data, test_data = np.split(model_data.sample(frac=1, random_state=1729), [int(0.7 * len(model_data)), int(0.9 * len(model_data))])   # Randomly sort the data then split out first 70%, second 20%, and last 10%
    
    pd.concat([train_data['y_yes'], train_data.drop(['y_no', 'y_yes'], axis=1)], axis=1).to_csv(f"{base_dir}/train/train.csv", index=False, header=False)
    pd.concat([validation_data['y_yes'], validation_data.drop(['y_no', 'y_yes'], axis=1)], axis=1).to_csv(f"{base_dir}/validation/validation.csv", index=False, header=False)
    pd.concat([test_data['y_yes'], test_data.drop(['y_no', 'y_yes'], axis=1)], axis=1).to_csv(f"{base_dir}/test/test.csv", index=False, header=False)

# ---
#     # Drop columns that are not required
#     df = df.drop(["mobile", "name"], axis=1)

#     # Shuffle the data
#     df = df.sample(frac=1)

#     # One hot encoding
#     df = pd.get_dummies(df, columns=['gender'])
    
#     #If required, save the id column    
# #     df.to_csv('output.csv', columns=["id"], index=False, header=False)
#     df = df.drop(["id"], axis=1)
    
#     # Split into train, validate, test data
#     rows = df.shape[0]
#     train = int(.7 * rows)
#     validate = int(.1 * rows)
#     test = rows-train-validate
    
#     # Save the files to local directory
#     df.iloc[:train].to_csv(f"{base_dir}/train/train.csv",
#                             index=False,header=False)
#     df.iloc[train:(train+validate)].to_csv(f"{base_dir}/validation/validation.csv",
#                             index=False,header=False)
#     df.iloc[(train+validate):].to_csv(f"{base_dir}/test/test.csv",
#                             index=False,header=False)
