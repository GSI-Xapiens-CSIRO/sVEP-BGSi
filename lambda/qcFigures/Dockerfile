FROM public.ecr.aws/lambda/python:3.12-x86_64

RUN dnf update -y && dnf install -y \
    gcc gcc-c++ make \
    blas-devel lapack-devel \
    openssl-devel \
    pkg-config \
    gzip \
    git \
    && dnf clean all

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"
ENV RUSTUP_HOME=/root/.rustup
ENV CARGO_HOME=/root/.cargo

RUN rustc --version && cargo --version

ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}/

COPY requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --upgrade pip wheel setuptools \
    && pip install -r requirements.txt --verbose

COPY lambda_function.py ${LAMBDA_TASK_ROOT}/
ADD shared ${LAMBDA_TASK_ROOT}/shared

CMD ["lambda_function.lambda_handler"]