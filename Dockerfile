# dockerfile for the language app
FROM python:3.10

# Set the working directory
WORKDIR /

RUN apt-get update && apt-get install -y --no-install-recommends python3-setuptools

# Update pip to the latest version
RUN python -m pip install --upgrade pip

# Copy the language app backend package into the container
COPY language_app_backend /language_app_backend

# Copy the requirements file into the container
COPY requirements.txt /requirements.txt

# Install the dependencies (including language_app_backend using "-e ./language_app_backend")
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the server package into the container
COPY server /

# Run using startup.bash
CMD ["bash", "startup.bash"]

# to build the image, run the following command in the terminal:
# docker build -t language_app:latest .
# to run the container, use the following command:
# docker run -p 8000:8000 language_app:latest