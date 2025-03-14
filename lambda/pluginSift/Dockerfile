FROM public.ecr.aws/lambda/provided:al2-x86_64

# Install system packages and perl
RUN yum update -y && \
    yum install -y java-21-openjdk python3 && \
    yum install -y aws-cli && \
    yum clean all

ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy files
COPY ./docker/main.py ./docker/SIFT4G_Annotator.jar ${LAMBDA_TASK_ROOT}/
COPY ./docker/bootstrap /var/runtime/bootstrap

# Make bootstrap executable
RUN chmod +x /var/runtime/bootstrap

# Define entry point
ENTRYPOINT ["/lambda-entrypoint.sh", "main.handler"]