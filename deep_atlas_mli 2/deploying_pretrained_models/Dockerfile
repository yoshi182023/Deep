# Start with the latest torchserve image
FROM pytorch/torchserve:latest

# Copy the model archive and config properties into the container
WORKDIR /workspace
COPY model_store /workspace/model_store
COPY config.properties /workspace

# Install git, to enable the installation of the CLIP model
USER root
RUN apt-get update
RUN apt-get install -y git

# Install the CLIP model
RUN /home/venv/bin/python3 -m pip install git+https://github.com/openai/CLIP.git

# Expose ports for inference, management, and metrics
EXPOSE 8080 8081 8082

# Start TorchServe
CMD ["torchserve", "--start", "--ncs", "--model-store", "/workspace/model_store", "--ts-config", "/workspace/config.properties", "--disable-token-auth"]
