FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && az version

# Install Terraform
ARG TF_VERSION=1.9.0
ARG TARGETARCH
RUN curl -fsSL "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_${TARGETARCH}.zip" -o /tmp/tf.zip \
    && unzip -q /tmp/tf.zip -d /usr/local/bin \
    && rm /tmp/tf.zip \
    && terraform version

# Install pytest + Azure SDK (substituindo boto3)
RUN pip install --no-cache-dir \
    pytest \
    azlocal \
    azure-identity \
    azure-mgmt-resource \
    azure-mgmt-compute \
    azure-mgmt-network \
    azure-mgmt-web \ 
    azure-storage-blob
RUN mkdir -p work
COPY . /work/ 
# Variáveis padrão para Azure (equivalente ao AWS env)
ENV AZURE_SUBSCRIPTION_ID="" \
    AZURE_TENANT_ID="" \
    AZURE_CLIENT_ID="" \
    AZURE_CLIENT_SECRET="" \
    TF_VAR_name_prefix=dev

WORKDIR /app