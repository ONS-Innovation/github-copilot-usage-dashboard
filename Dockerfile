FROM public.ecr.aws/lambda/python:3.12

# Install git using dnf (https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-base)
# For python 3.12, dnf replaces yum for package management
RUN dnf install git -y

# Copy required files into the container
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install poetry

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root

# Copy the source code into the container
COPY src/ src/

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "src.main.handler" ]