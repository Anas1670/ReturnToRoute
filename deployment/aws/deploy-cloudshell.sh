#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""
cd "$(dirname "$0")"

for cmd in aws python3 curl; do command -v "$cmd" >/dev/null || { echo "STOP: Missing $cmd in CloudShell."; exit 1; }; done
echo "STEP 1/5 — Checking the AWS Academy session"
aws sts get-caller-identity --query Arn --output text
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region || true)}}"
[ -n "$REGION" ] || { echo "STOP: No AWS region. Set AWS_DEFAULT_REGION first."; exit 1; }
export AWS_DEFAULT_REGION="$REGION"
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
if [ -z "$VPC" ] || [ "$VPC" = None ]; then
  echo "STOP: No default VPC in $REGION. No resources were changed."
  exit 1
fi
SUBNET_JSON=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC" --output json)
mapfile -t SUBNETS < <(printf '%s' "$SUBNET_JSON" | python3 -c '
import json,sys,os
rows=json.load(sys.stdin)["Subnets"]
region=os.environ.get("AWS_DEFAULT_REGION", "")
# AWS reported that t3.micro is unavailable in us-east-1e. Use only
# the supported zones AWS returned for us-east-1; keep other regions flexible.
supported_east={"us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d", "us-east-1f"}
web_candidates=[s for s in rows if s["MapPublicIpOnLaunch"] and
                (region!="us-east-1" or s["AvailabilityZone"] in supported_east)]
web_candidates.sort(key=lambda s:(s["AvailabilityZone"],s["SubnetId"]))
azs={}
for s in sorted(rows,key=lambda s:(s["AvailabilityZone"],s["SubnetId"])):
    azs.setdefault(s["AvailabilityZone"],s["SubnetId"])
if web_candidates and len(azs)>=2:
    web=web_candidates[0]
    print("EC2 public subnet zone: "+web["AvailabilityZone"],file=sys.stderr)
    print(web["SubnetId"])
    print(*list(azs.values())[:2],sep="\n")
')
if [ "${#SUBNETS[@]}" -ne 3 ]; then
  echo "STOP: Need a public subnet and two subnet availability zones."
  exit 1
fi
STACK=rtr-demo
if aws cloudformation describe-stacks --stack-name "$STACK" >/dev/null 2>&1; then
  echo "STOP: Stack '$STACK' already exists. No resources were changed."
  aws cloudformation describe-stacks --stack-name "$STACK" --query 'Stacks[0].[StackStatus,Outputs]' --output json
  exit 1
fi

echo "STEP 2/5 — Validating the CloudFormation template"
aws cloudformation validate-template --template-body file://cloudformation.yaml >/dev/null

echo "STEP 3/5 — Uploading the application package privately"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="rtr-demo-$ACCOUNT-$REGION"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  if [ "$REGION" = us-east-1 ]; then
    aws s3api create-bucket --bucket "$BUCKET" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
  fi
fi
aws s3 cp app_bundle.zip "s3://$BUCKET/app_bundle.zip" --only-show-errors
URL=$(aws s3 presign "s3://$BUCKET/app_bundle.zip" --expires-in 7200)
DBPASS=$(python3 -c 'import secrets,string; a=string.ascii_letters+string.digits; print("".join(secrets.choice(a) for _ in range(36)))')
SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(48))')

echo "STEP 4/5 — Creating EC2 and private RDS (usually 10–20 minutes)"
aws cloudformation create-stack --stack-name "$STACK" --template-body file://cloudformation.yaml \
  --parameters \
  "ParameterKey=VpcId,ParameterValue=$VPC" \
  "ParameterKey=PublicSubnetId,ParameterValue=${SUBNETS[0]}" \
  "ParameterKey=DbSubnetA,ParameterValue=${SUBNETS[1]}" \
  "ParameterKey=DbSubnetB,ParameterValue=${SUBNETS[2]}" \
  "ParameterKey=AppZipUrl,ParameterValue=$URL" \
  "ParameterKey=DbPassword,ParameterValue=$DBPASS" \
  "ParameterKey=AppSecret,ParameterValue=$SECRET" >/dev/null
unset DBPASS SECRET URL
if ! aws cloudformation wait stack-create-complete --stack-name "$STACK"; then
  echo "STOP: AWS infrastructure creation failed. Recent events:"
  aws cloudformation describe-stack-events --stack-name "$STACK" --query 'StackEvents[0:12].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' --output table
  exit 1
fi
WEB_URL=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='Website'].OutputValue | [0]" --output text)

echo "STEP 5/5 — Waiting for the Flask application to start"
for attempt in $(seq 1 60); do
  if curl -fsS --connect-timeout 2 --max-time 5 "$WEB_URL/login" -o /dev/null 2>/dev/null; then
    echo "SUCCESS — RETURN-TO-ROUTE IS LIVE"
    echo "OPEN ON ANY DEVICE: $WEB_URL"
    echo "Only use fictional demo credentials. HTTP is not encrypted."
    exit 0
  fi
  sleep 10
done
echo "WARNING: EC2/RDS were created, but the app is not responding."
echo "Check the EC2 console system log for 'rtr-install'."
echo "URL: $WEB_URL"
exit 1
