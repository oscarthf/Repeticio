# dockerfile for the language app
FROM python:3.10

RUN apt-get update && apt-get install -y --no-install-recommends python3-setuptools

# Copy the requirements file into the container
COPY requirements.txt /app/requirements.txt

# Update pip to the latest version
RUN python3 -m pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Install the dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the language app backend package into the container
COPY language_app_backend /app/language_app_backend

# Set the working directory
WORKDIR /app/language_app_backend

# Install the language app backend package
RUN python3 -m pip install .

# Remove the other files which were copied into the container
RUN rm -rf /app/language_app_backend && \
    rm -rf /app/requirements.txt

# Copy the server package into the container
COPY server /app

# Set the working directory to the server package
WORKDIR /app/server

# Run using startup.bash
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "language_app.wsgi:app"]

# to build the image, run the following command in the terminal:
# docker build -t language_app:latest .
# to run the container, use the following command:
# docker run -p 8000:8000 language_app:latest