# dockerfile for the language app
FROM python:3.10-slim

# Copy the requirements file into the container
COPY requirements.txt /app/requirements.txt

# Update pip to the latest version
RUN pip install --upgrade pip

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the language app backend package into the container
COPY language_app_backend /app/language_app_backend

# Set the working directory
WORKDIR /app/language_app_backend

# Install the language app backend package
RUN pip install .

# Copy the server package into the container
COPY server /app/server

# Set the working directory to the server package
WORKDIR /app/server

# Run using startup.bash
CMD ["bash", "startup.bash"]