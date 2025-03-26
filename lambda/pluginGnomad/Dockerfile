FROM public.ecr.aws/lambda/python:3.12-x86_64

# Install system dependencies
RUN dnf update -y && dnf install -y \
    gcc gcc-c++ make \
    blas-devel lapack-devel \
    openssl-devel \
    pkg-config \
    git \
    java-11-amazon-corretto \
    procps \
    && dnf clean all

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Set Lambda task root
ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

# Install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --upgrade pip wheel setuptools \
    && pip install -r requirements.txt --verbose

RUN rm -f /var/runtime/bootstrap

# Copy necessary files
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/
COPY bootstrap /var/runtime/bootstrap

# Make bootstrap executable
RUN chmod +x /var/runtime/bootstrap

# Define entry point
ENTRYPOINT ["/lambda-entrypoint.sh", "lambda_function.lambda_handler"]
