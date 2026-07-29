#!/bin/bash
DOCKER_IMAGE="terraform-worker-image"
CONTAINER_NAME="terraform-worker"
repo_dir=.
name_prefix="tf-$(echo "$$$(date +%s)")"

wait_for_localstack() {
  local endpoint="${LOCALSTACK_ENDPOINT:-http://localhost:4566/_localstack/health}"
  local timeout_seconds="${LOCALSTACK_READY_TIMEOUT:-45}"
  local waited=0

  echo "Waiting for LocalStack health endpoint: $endpoint"
  while [[ $waited -lt $timeout_seconds ]]; do
    if curl -fsS "$endpoint" >/dev/null 2>&1; then
      echo "LocalStack is healthy."
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done

  echo ""
  echo "ERROR: LocalStack is not available."
  echo "  Health check timed out after ${timeout_seconds}s at ${endpoint}"
  echo "  Ensure LocalStack is running, reachable, and LOCALSTACK_AUTH_TOKEN is correctly set."
  echo ""
  return 1
}
docker compose up -d --force-recreate
wait_for_localstack
docker build -t $DOCKER_IMAGE .

if docker ps --filter "name=$CONTAINER_NAME" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Removing existing worker container to avoid stale state: $CONTAINER_NAME"
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi
echo "Starting worker container: $CONTAINER_NAME"
docker run -d \
--platform=linux/amd64 \
--name "$CONTAINER_NAME" \
-v "$repo_dir:/work-ro:ro" \
--network host \
-e "TF_VAR_name_prefix=$name_prefix" \
-e "AZURE_SUBSCRIPTION_ID=""" \
-e "AZURE_TENANT_ID=""" \
-e "AZURE_CLIENT_ID=""" \
-e "TF_VAR_name_prefix=dev""" \
"$DOCKER_IMAGE" \
bash -c "mkdir -p /work && tail -f /dev/null"

exec_in_container() {
  docker exec -w /work "$CONTAINER_NAME" bash -c "$*"
}

failed=0

run_step() {
  local description="$1"
  local command="$2"

  echo "$description"
  if ! exec_in_container "$command"; then
    failed=1
  fi
}

run_step "Running terraform fmt -check..." 'terraform fmt -check -diff'
run_step "Running terraform init..." 'terraform init -input=false -backend=false'
run_step "Running terraform validate..." 'terraform validate'
run_step "Running terraform plan" 'terraform plan -input=false -detailed-exitcode -out=.tfplan'
run_step "Change plan to json" 'terraform show -json .tfplan > plan.json'
run_step "Running Unit Tests" 'pytest -v tests/unit_tests.py'
run_step "Apply from tfplan" 'terraform apply -input=false .tfplan'
run_step "Running Integration Tests" 'sleep 60 && pytest -v tests/integration_tests.py'
run_step "Planning destroy" 'terraform plan -destroy -input=false -out=destroy.tfplan'
#run_step "Terraform Destroy" 'terraform apply -input=false destroy.tfplan'