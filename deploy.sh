#!/bin/bash

# --- 部署/基礎設施參數 (Deployment/Infra Config) ---
export REGION="us-central1"
export IMAGE_REPO="cloud-run-psc-repo"
export IMAGE_NAME="mongo-psc-verifier"
# 每次部署手動更新或由 CI/CD 流程自動產生
export IMAGE_TAG="v3.0" 

# 自動計算最終路徑
export GCP_PROJECT_ID=$(gcloud config get-value project)
export IMAGE_PATH="${REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${IMAGE_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

# --- 應用程式配置 (App Config - 非機敏) ---
export AUTHOR_NAME='cyceve0'
export MONGO_DB_NAME='etl_monitoring'
export JOB_NAME="mongo-psc-verifier-job"

# --- 部署/執行指令 ---
# 1. 建置並推送容器
gcloud builds submit . --tag $IMAGE_PATH

# 2. 部署 Cloud Run Job
gcloud run jobs deploy $JOB_NAME \
  --image "$IMAGE_PATH" \
  --region "$REGION" \
  --vpc-connector cloud-run-psc-connector \
  --vpc-egress all \
  --set-secrets MONGO_URI="MONGO_ATLAS_URI:latest" \
  --set-env-vars AUTHOR_NAME="$AUTHOR_NAME",MONGO_DB_NAME="$MONGO_DB_NAME" \
  --task-timeout 60s
