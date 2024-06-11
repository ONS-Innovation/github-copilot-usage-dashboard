# Get a base image with a slim version of Python 3.10
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make run_script.sh executable
RUN chmod +x /app/run_script.sh

# Install AWS CLI
RUN pip install awscli

# Install the required packages
RUN pip install -r requirements.txt

# Run the run_script.sh script
# Note: ENTRYPOINT cannot be overriden by docker run command
ENTRYPOINT ["/app/run_script.sh"]