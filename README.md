# Return-to-Route — AWS Deployment

## Deployment
1. Open AWS CloudShell in us-east-1.
2. Upload ReturnToRoute_AWS_Deployment.zip (Please download it from the repository located in the same folder as this readme.)
3. Execute the following commands:

    unzip -o ReturnToRoute_AWS_Deployment.zip
    cd ReturnToRoute_Deploy_Kit
    bash deploy-cloudshell.sh

4. Open the website URL displayed after deployment completes.

Deployment may take approximately 15–30 minutes.

## Testing
Register a customer or staff account. Sample data is generated automatically upon registration. Use fictional credentials only, as the demonstration uses HTTP.

## Cleanup
Delete the CloudFormation stack:
