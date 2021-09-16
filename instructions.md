# Detailed instructions for setting up the environment

Note: This guide will setup a new VPC with a private and public subnet.

## Content
- [Allocate elastic IP](#Allocate-elastic-IP)
- [Create SageMaker Studio](#Create-SageMaker-Studio)
- [Assign IAM permission](#Assign-IAM-permission)
- [Create SageMaker Studio user](#Create-SageMaker-Studio-user)
- [SageMaker Studio](#SageMaker-Studio)

## Allocate elastic IP
- Login to your AWS management console and go to VPC.
- On the left side, click on `Elastic IPs`.
- At the right side, click on `Allocate Elastic IP address`.

![VPC](img/vpc1.png)

- Leave the settings as is and click `Allocate`.

![VPC](img/vpc2.png)

- On the left side, click on `VPC Dashboard`.
- Click on `Launch VPC Wizard`.

![VPC](img/vpc3.png)

- Select the second option `VPC with Public and Private Subnets` and click `Select`.

![VPC](img/vpc4.png)

- Leave the settings as is. Under `VPC name`, enter a name of your choice. If you change the `Private subnet name`, do take note of it as you need to change it in notebook 01.

![VPC](img/vpc5.png)

---

## Create SageMaker Studio
- In your AWS management console, go to SageMaker.
- On the left side, click on `Amazon SageMaker Studio`.
- At the `Get started` page, choose `Standard setup` and choose `AWS Identity and Access Management (IAM)`
- Click on the `Choose an IAM role` box

![create-studio](img/create-studio1.png)

- `Create a new role`

![create-studio](img/create-studio2.png)

- For this demo, we allow access to every S3 bucket. Click on `Create role`.

![create-studio](img/create-studio3.png)

- This will create an IAM role. 

![create-studio](img/create-studio4.png)

- Scrolling down, leave the `Notebook sharing configuration` and `SageMaker Projects and JumpStart` as default.
- Under `Network and storage`, choose the VPC that you have created (default is ok) and choose at least one subnet. 
- Under `Network Access for Studio`, ensure `VPC Only` is selected.
- Under `Security group(s)`, choose the security group that allows access between SageMaker Studio and RedShift. The default security group is ok.
- The screen should look like this

![create-studio](img/create-studio5.png)

- Click `Submit`. If you have any error, the submit button will not work. Scroll up to check on the error. One error I encountered is that the IAM role is not selected properly and I had to reselect it again.
---

## Assign IAM permission
- While waiting, the next step is to assign additional policy to the SageMaker role.
- In your AWS management console, go to IAM.
- On the left side, click on `Roles`.
- Select the SageMaker role that was created earlier. Mine is listed below and yours will differ.

![create-studio](img/create-studio6.png)

- Notice there are two policies given to this role. Click on `Attach policies`.

![create-studio](img/create-studio7.png)

- Enter `iamfull` in the search box. Check the `IAMFullAccess` policy and click `Attach policy`.

![create-studio](img/create-studio8.png)

- This should return back to the IAM role page. Note there are three policies given to this role now.

![create-studio](img/create-studio9.png)
---

## Create SageMaker Studio user
- In your AWS management console, go to SageMaker.
- On the left side, click on `Amazon SageMaker Studio`.
- Under the `Studio Summary`, the status should show `Ready`.
- Click on `Add user`.

![create-studio](img/create-studio10.png)

- Enter your desired user name or accept the default one.
- For the execution role, ensure the SageMaker role created earlier is selected.

![create-studio](img/create-studio11.png)

- Click on `Submit`.
- Once the user is created, click on `Open Studio`.

![create-studio](img/create-studio12.png)


## SageMaker Studio
- After a short while, you will be presented with the following screen.

![studio](img/studio1.png)

- On the left side, click on the second icon and click on `Clone a Repository`. 

![studio](img/studio2.png)

- Enter the git clone URL of this repo and click `CLONE`.

![studio](img/studio3.png)

- On the left side, click on the last icon. At the menu box, select `Projects` if it is not selected.

![studio](img/studio4.png)

- Click on `Create project`. A new window should pop up on the right side.
- Select the `MLOps template for model building, training and deployment` and click `Select project template`.

![studio](img/studio5.png)

- Enter a name for the project and click `Create project`.

![studio](img/studio6.png)

- After a while, the project is created.
- Click on the first `clone repo...`.

![studio](img/studio7.png)

- Click on `Clone Repository` to clone the repo to the SageMaker Studio.

![studio](img/studio8.png)

- Click on the second `clone repo...` and click `Clone Repository`.

![studio](img/studio9.png)

- The window should look like this.

![studio](img/studio10.png)

- Click on the `Local path` link beside the modelbuild repo. This will bring you to the directory.

![studio](img/studio11.png)

- Select all the files, right click and click `Delete`.

![studio](img/studio12.png)

- Go to the repo that was clone earlier (`bankdemo-build` in my case). Your repo name may differ.
- Select all the files, right click and click `Cut`. SageMaker Studio does not allow you to copy folders but cut is ok.

![studio](img/studio12.png)

- On the right side, if the BankDemo2 screen is still open, you can click on the `Local path` link beside the modelbuild repo. This will bring you to the directory.

![studio](img/studio13.png)

- Right click and click `Paste`.

![studio](img/studio14.png)

- The files will be moved here. Do not navigate away from this folder. Note that the files in your directory may differ from the screenshot.

![studio](img/studio15.png)

- On the left side, click on the second icon. Scroll your mouse to the right of `Changed`, select the `+` to track all files. Repeat the same for `Untracked`.

![studio](img/studio16.png)

- Your window should look like this where there are no files under `Changed` and `Untracked`. The number of files shown may differ from yours.
- Enter a commit message (commit in the screenshot) and click `Commit`.

![studio](img/studio17.png)

- Enter your name, email and click `OK`.

![studio](img/studio18.png)

- Click on the icon with an up arrow to push the changes. This icon is above the green line in the screenshot.

![studio](img/studio19.png)

- You will get the following message.

![studio](img/studio20.png)

- On the right side of the screen, click on `Pipelines` tab and double click on the Pieplines shown (`BankDemo2-p-sn41sxosn3ef` in my case).

![studio](img/studio21.png)

- The pipeline should automatically run after a short while as you push new codes. Do note that this pipeline will fail as you have not setup RedShift.

![studio](img/studio22.png)

# This concludes setting up SageMaker Studio. You can now proceed to run notebook 01.


```python

```
