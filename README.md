# Return-to-Route — AWS Deployment

## Deployment
1. Open AWS CloudShell in us-east-1.
2. Download ReturnToRoute_AWS_Deployment.zip from the repository which is in the same folder as this README.
3. Upload ReturnToRoute_AWS_Deployment.zip to AWS CloudShell. This zip file contains the complete application source code and deployment scripts required to automatically provision the Amazon EC2 instance and Amazon RDS PostgreSQL database used by the application.
4. Execute the following commands:

    unzip -o ReturnToRoute_AWS_Deployment.zip
   
    cd ReturnToRoute_Deploy_Kit
   
    bash deploy-cloudshell.sh

5. Open the website URL displayed after deployment completes.

Deployment may take approximately 15–30 minutes.

## Testing
Register a customer or staff account. Sample data is generated automatically upon registration. Use fictional credentials only, as the demonstration uses HTTP.

## Cleanup
Delete the CloudFormation stack:
