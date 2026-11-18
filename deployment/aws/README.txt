RETURN-TO-ROUTE — AWS ACADEMY DEPLOYMENT KIT (v4 — AZ and Python compatibility corrections)
================================================
Contents:
  cloudformation.yaml  -> public EC2 web server and PRIVATE PostgreSQL RDS
  app_bundle.zip       -> current Flask source, 500 products, empty database schema
  deploy-cloudshell.sh -> CloudShell automation and website health check

EXACT DEPLOYMENT STEPS
1. Start a NEW AWS Academy Learner Lab session and open its AWS Console.
2. Select AWS region US East (N. Virginia), us-east-1, then open CloudShell.
   The previous failure was an unsupported Availability ZONE (us-east-1e),
   not an incorrect region. This kit avoids us-east-1e for t3.micro.
   Also corrected: Amazon Linux 2023 defaults to Python 3.9; the pinned
   Flask dependencies require Python 3.10+, so the installer uses Python 3.11.
3. CloudShell Actions > Upload file > select ReturnToRoute_AWS_Deploy_Ready_v4.zip
   from your Mac's Downloads folder. Wait for upload success.
4. Paste the following three lines into AWS CloudShell:

unzip -o ReturnToRoute_AWS_Deploy_Ready_v4.zip
cd ReturnToRoute_Deploy_Kit
bash deploy-cloudshell.sh

5. Keep CloudShell open. It prints the PUBLIC website URL once /login works.
   Log in/register using FICTIONAL customer and staff data only.
   A newly registered customer gets 20 sample purchased items.
   A newly registered staff member gets 50 assigned sample returns.
   Return history and decisions persist while this RDS instance exists.

REALISTIC TIMING
RDS initialization itself often takes 10–20 minutes, plus Python installation.
This is one command-driven deployment, but not an instant few-minute launch.
Every NEW lab requires fresh EC2/RDS creation and demo data initialization.
Do not rerun the script if the stack already exists; it will stop safely.
CloudFormation stack success is NOT the same as successful app startup;
the helper separately checks the website.

IF THE SCRIPT REPORTS STOP OR ERROR
Copy the complete final error and send it back. Do not create random resources
in the console. We will correct the specific restriction/error.
AWS Academy accounts vary: CloudShell, S3, CloudFormation, EC2, RDS,
and t3.micro/db.t3.micro must be permitted. No live AWS deployment was
performed during this kit's build.

SAFETY / DEMO ONLY
HTTP port 80 is public; traffic is not encrypted. Do not type real passwords
or personal information. The bundled app permits public staff sign-up, so
it is not hardened for an unrestricted production launch. PostgreSQL RDS is
private to the EC2 security group. Credentials are generated per deployment,
but the EC2 initialization data may still be visible to AWS account operators.
Demo records are simulated; this does not make real payments/refunds.

AFTER THE PRESENTATION
The Learner Lab may destroy resources when it ends. To intentionally remove the
stack sooner, AWS CloudShell command: aws cloudformation delete-stack --stack-name rtr-demo
This deletes the RDS database, including all demo accounts and decisions.
The S3 object/bucket are NOT deleted automatically by that command.
