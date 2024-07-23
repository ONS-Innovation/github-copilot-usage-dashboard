FROM public.ecr.aws/lambda/python:3.12

# Install git using dnf (https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-base)
# For python 3.12, dnf replaces yum for package management
RUN dnf install git -y

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY main.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.handler" ]