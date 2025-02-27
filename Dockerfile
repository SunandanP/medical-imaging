# Use the official Frappe Worker image as the base
FROM frappe/frappe-worker:latest

# Set environment variables
ENV BENCH_NAME=medical-imaging-bench \
    FRAPPE_BRANCH=version-15 \
    SITE_NAME=bloodcell.calssify \
    ADMIN_PASSWORD=root \
    MARIADB_ROOT_PASSWORD=root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a new bench
RUN bench init ${BENCH_NAME} --frappe-branch ${FRAPPE_BRANCH} --python /usr/bin/python3

# Switch to the bench directory
WORKDIR /home/frappe/${BENCH_NAME}

# Copy the custom app (medical-imaging) into the bench
COPY ./apps/medical-imaging ./apps/medical-imaging

# Install the custom app
RUN bench get-app medical-imaging ./apps/medical-imaging \
    && bench --site ${SITE_NAME} install-app medical-imaging

# Install app-specific dependencies (if any)
RUN cd apps/medical-imaging && pip install -r requirements.txt

# Download model files (if required)
RUN mkdir -p apps/medical-imaging/medical_imaging/prediction_models \
    && cd apps/medical-imaging/medical_imaging/prediction_models \
    && wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1LMQNx2ajKGsGpxA1PBW0_Im3MDmWR5_M" -O EfficientNetB4.pth \
    && wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1BbFdIfvJPiPUl0kzUFiayiws6tXEEgYJ" -O fasterrcnn_model_v2.pth

# Expose ports
EXPOSE 8000

# Start the bench
CMD ["bench", "start"]