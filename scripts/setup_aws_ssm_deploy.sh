#!/usr/bin/env bash
# GitHub Actions → ECR → SSM 배포에 필요한 AWS 리소스를 만든다. (AWS CloudShell 에서 실행)
# 여러 번 실행해도 안전하다 (이미 있으면 건너뜀).
#
#  - ECR 저장소 sign-backend (최근 이미지 10개만 보관)
#  - 배포 전용 IAM 사용자 github-actions-sign-deploy (권한: ECR 푸시 + 이 인스턴스 SSM 명령 실행만)
#      조직 SCP 가 GitHub OIDC 공급자 생성을 막고 있어 액세스 키 방식을 쓴다.
#      액세스 키는 이 스크립트가 만들지 않는다. 콘솔에서 직접 발급해 GitHub 시크릿에 등록한다.
#  - EC2 역할 sign-ec2-role (SSM 관리 + ECR 읽기) 을 인스턴스에 연결
set -euo pipefail

ACCOUNT_ID=549303709378
REGION=ap-southeast-2
INSTANCE_ID=i-06f91de78a10949a6
ECR_REPO=sign-backend
DEPLOY_USER=github-actions-sign-deploy
EC2_ROLE=sign-ec2-role
EC2_PROFILE=sign-ec2-profile

echo "[1/4] ECR 저장소"
aws ecr describe-repositories --region $REGION --repository-names $ECR_REPO >/dev/null 2>&1 \
  || aws ecr create-repository --region $REGION --repository-name $ECR_REPO \
       --image-scanning-configuration scanOnPush=true >/dev/null
aws ecr put-lifecycle-policy --region $REGION --repository-name $ECR_REPO --lifecycle-policy-text '{
  "rules": [{"rulePriority": 1, "description": "keep last 10 images",
    "selection": {"tagStatus": "any", "countType": "imageCountMoreThan", "countNumber": 10},
    "action": {"type": "expire"}}]}' >/dev/null

echo "[2/4] 배포 전용 IAM 사용자"
aws iam get-user --user-name $DEPLOY_USER >/dev/null 2>&1 \
  || aws iam create-user --user-name $DEPLOY_USER >/dev/null

echo "[3/4] 배포 권한 (ECR 푸시 + SSM 명령)"
cat > /tmp/deploy-policy.json <<EOF
{"Version": "2012-10-17", "Statement": [
  {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
  {"Effect": "Allow", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:CompleteLayerUpload",
     "ecr:GetDownloadUrlForLayer", "ecr:InitiateLayerUpload", "ecr:PutImage", "ecr:UploadLayerPart"],
   "Resource": "arn:aws:ecr:$REGION:$ACCOUNT_ID:repository/$ECR_REPO"},
  {"Effect": "Allow", "Action": "ssm:SendCommand",
   "Resource": ["arn:aws:ec2:$REGION:$ACCOUNT_ID:instance/$INSTANCE_ID",
                "arn:aws:ssm:$REGION::document/AWS-RunShellScript"]},
  {"Effect": "Allow", "Action": ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"], "Resource": "*"}
]}
EOF
aws iam put-user-policy --user-name $DEPLOY_USER --policy-name sign-deploy --policy-document file:///tmp/deploy-policy.json

echo "[4/4] EC2 인스턴스 역할 (SSM + ECR 읽기)"
aws iam get-role --role-name $EC2_ROLE >/dev/null 2>&1 \
  || aws iam create-role --role-name $EC2_ROLE --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
aws iam attach-role-policy --role-name $EC2_ROLE --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name $EC2_ROLE --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
aws iam get-instance-profile --instance-profile-name $EC2_PROFILE >/dev/null 2>&1 || {
  aws iam create-instance-profile --instance-profile-name $EC2_PROFILE >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name $EC2_PROFILE --role-name $EC2_ROLE
  sleep 10  # IAM 전파 대기
}
CURRENT=$(aws ec2 describe-iam-instance-profile-associations --region $REGION \
  --filters Name=instance-id,Values=$INSTANCE_ID --query 'IamInstanceProfileAssociations[0].IamInstanceProfile.Arn' --output text)
if [ "$CURRENT" = "None" ]; then
  aws ec2 associate-iam-instance-profile --region $REGION --instance-id $INSTANCE_ID \
    --iam-instance-profile Name=$EC2_PROFILE >/dev/null
fi

echo "완료"
echo "  배포 사용자: $DEPLOY_USER (액세스 키는 IAM 콘솔에서 직접 발급)"
echo "  ECR: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO"
