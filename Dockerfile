# Get a base image with a slim version of Python 3.10
FROM python:3.12-slim

# run a pip install for poetry 1.5.0
RUN pip install poetry==1.5.0

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Run poetry install --without dev
RUN poetry install --no-root 

# Expose the port the app runs on
EXPOSE 8501

# Run the dashboard
# Note: ENTRYPOINT cannot be overriden by docker run command
ENTRYPOINT ["poetry", "run", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]