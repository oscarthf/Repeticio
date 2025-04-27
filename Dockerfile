# dockerfile for the language app
FROM python:3.10

# Set the working directory
WORKDIR /

# Copy everything to the working directory
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends python3-setuptools

# Update pip to the latest version
RUN python -m pip install --upgrade pip

# Install the dependencies (including language_app_backend using "-e ./language_app_backend")
RUN python -m pip install --no-cache-dir -r requirements.txt

# Run using startup.bash
CMD ["bash", "startup.bash"]

# to build the image, run the following command in the terminal:
# docker build -t language_app:latest .
# to run the container, use the following command:
# docker run -p 8000:8000 language_app:latest