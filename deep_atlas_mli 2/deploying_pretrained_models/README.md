Key Takeaways
1. MLOps as the Backbone of the ML Lifecycle
Big Picture: MLOps extends DevOps into machine learning, ensuring smooth transitions across data ingestion, model development, deployment, and monitoring.
Why It Matters: Without structured handoffs and reproducible pipelines, models degrade quickly or fail to scale in production.
Consider: How would your team’s productivity change if data, models, and deployment environments weren’t standardized?
2. Data as the Starting Point
Core Insight: Data ingestion, preparation, and feature engineering are prerequisites for meaningful modeling.
How It Connects: Garbage in, garbage out — high-quality, version-controlled data underpins reliable models.
Practice: Use tools like Pachyderm (or simple folder structures with metadata) to keep track of dataset versions.
So What?: Losing track of which dataset trained which model undermines reproducibility and governance.
3. Experiment Tracking & Reproducibility
Framework: Tools like Weights & Biases or Neptune AI log experiments, hyperparameters, and performance curves.
Reasoning Process: Unlike static code, ML models evolve through many iterations — history matters.
Analogy: Think of experiment tracking as version control for scientific discovery, not just software.
Problem to Solve: How would you defend your model choices six months later without experiment logs?
4. Automation Through Orchestration Pipelines
Concept: Orchestration tools (Airflow, MLflow, Kubeflow, Metaflow, ZenML) automate workflows and enforce consistency.
Key Decision Point: Choose triggers (manual vs automatic) carefully, since retraining frequency balances cost with model freshness.
Pitfall: Failing to separate pipelines by environment (data, training, inference) leads to brittle systems.
Transferable Insight: Any repetitive process that requires reliability benefits from automation.
5. Deployment and Monitoring as Continuous Loops
Deployment Breakdown: Export → Registry → Deployment (e.g., TorchServe, Docker, EC2).
Monitoring Focus: Beyond latency and throughput, track model drift and data drift to detect performance decay.
Generative Models Twist: Standard metrics often fail — user feedback loops (thumbs up/down) become critical.
So What?: Deployment isn’t an endpoint; it’s the beginning of continuous quality assurance.
6. Governance, Checkpointing, and Compliance
Checkpointing: Save serialized snapshots of models to resume training or recover from failures.
Governance: Logging datasets and training processes is essential for audits (e.g., legal disputes about training data).
Practical Relevance: Without checkpoints, model recovery is costly. Without logs, compliance is impossible.
7. Platforms and Advanced Considerations
Full-Service Platforms: Amazon SageMaker, Google Vertex, and AutoML provide end-to-end solutions for teams with varied expertise.
Distributed Training: Tools like Ray enable parallelization across GPUs, crucial for large models.
Training Paradigms: Batch vs online training trade off stability vs adaptability.
Deployment Targets: Models may need to run in cloud APIs, mobile apps, or local inference — ONNX and CoreML bridge these.
So What?: Platform choice and deployment strategy determine scalability and accessibility.
8. From Notebooks to Production Pipelines
Core Shift: Notebooks are great for exploration but fragile in production.
Tooling: Systems like Kale help convert notebooks into Kubeflow pipelines.
Misconception: Productionizing ML is just about “exporting code” — in reality, it’s about building reproducible, automated systems.
Deploying pre-trained models
Get started by clicking 'download' and moving the downloaded content into your main coursework folder. You'll need these files to complete the exercise.

Objectives:

Delve into working with ML models by deploying two pre-trained models
Note the workflow involved in downloading, packaging, and running models
Note the resources and hardware requirements of running small and large models
Context
Note: This exercise has two sections:

Deploying Densenet-161 on an AWS EC2 instance
Deploying CLIP with custom TorchServe handlers
We will first deploy a pre-trained PyTorch model, the Densenet-161 image classifier, to an AWS EC2 instance. DenseNet161 can sort images into about 1000 pre-defined classes.

Later in the exercise, we will upgrade our deployment to also use OpenAI's CLIP model which is much larger but also capable of classifying images into arbitrary classes.

Deploying Densenet-161 on an AWS EC2 instance
We're going to use an AWS instance to host the inference server for a pretrained model. (We assume you've created an AWS account already during the Environment Setup process at the beginning of this course.) AWS products, including EC2, can be found in the "Services" menu, at the top of the AWS Management Console's EC2 dashboard page.

On that page, find the option to initiate the process of launching a new instance.

Give it a name like "Deep Atlas Coursework Server"
Choosing an Amazon Machine Instance Type
In general, it's a good idea to use one of the Deep Learning AMI's, which are already very well configured for use with each of the major ML frameworks. Though they can't be used with the free tier, they're still pretty cheap. If you try to configure machines yoruself, there are countless ways to get your dev ops steps wrong, making every step harder.

Even so, in this exercise we're going to take the hard road, and configure the machine for ML ourselves. This will give us experience closer to the metal, which we'll need down the road anyway if we ever work with (or have to build!) complex ML Ops pipelines. Let's limit ourselves to the free tier and see where it gets us.

NOTE: In the future, we recommend you select the Deep Learning AMI (PyTorch 2.x) to keep your life simple, even though it requires more storage and hardware than the free-tier allows.

Choose one of the following Application/OS images (AMIs):
Ubuntu (recommended)
Amazon Linux (should work!)
Configuring Your Instance For Launch
For the instance type, a free-tier t2-micro will suffice (you may choose a different one; be mindful of the hourly rates)
The second portion of this exercise will present higher memory requirements. You will need a t2.medium or more.
Create a new key-pair login if necessary and download the key-file to a secure location on your computer. Do NOT check this into git!
In the Network Settings, allow SSH, HTTP, and HTTPS traffic to your server (SSH for administration, and HTTP/S for inference tasks)
Choose the maximum amount of storage available in the free tier (30GB) or more if it's required by your AMI (~45GB for the DL AMI)
Click "Launch Instance", and connect to it from your local terminal
In the dashboard's sidebar, navigate to Instances (section) > Instances (menu item) > [click on the instance ID, a link] > Connect > "SSH client" tab
Follow Amazon's instructions for connecting
Setting Up Your Newly Launched Image
Installing Conda
NOTE: You only need to install Conda if you are on the free-tier, and did not use a Deep Learning AMI

Install conda, which is an alternative to pip preferred by the PyTorch ecosystem. The second command will offer a series of interactive prompts. In that process, you can accept the defaults, except for one:

Select "yes" when prompted to activate conda automatically after starting a shell (otherwise, you will have to run conda activate every time you ssh into your instance).
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh Miniconda3-latest-Linux-x86_64.sh
Per the onscreen instructions, you will need to close and reopen your shell to activate conda.

type exit
use the same ssh command to re-connect to your ec2 instance (you may be able to press the 'up' key to recall that command).
You can then verify that conda is working by running conda --version.
Installing Dependencies with Conda
The dependencies we are using — particularly PyTorch — require Python 3.11. Linux ships with Python 3.12 by default. Conda will allow us to downgrade:

conda install python=3.11
Now we need to install PyTorch and its related libraries:

conda install pytorch torchvision torchaudio cpuonly -c pytorch
TorchServe and Model Archive Files
TorchServe is a library that can expose PyTorch models via a web server, with automatically generated API, logging, metrics, and model versioning capabilities.

To do this, you must first get TorchServe to create a model archive file for your target model, in the state you want to run it. A model archive file is a compressed representation of a trained model, ready to be run on an inference server. Having one allows you to treat the trained model as a well-functioning black box of prediction. Without it, you would have to manually load up the model architecture from the original source files that defined it, then load the parameters into an instance of that model architecture object.

In the simplest case, creating a model archive requires 3 inputs:

A model definition (a Python model.py file that defines the model class)
A model's "state dict" (a .pth or .pt file that contains all the parameters of a model, saved separately)
A index_to_name JSON file which maps the index of the model's output to a human-readable label. With it, instead of seeing which indices correspond to the highest probabilities, we can see label names.
Set Up the Inputs to the Model Archiving Process
Let's start by installing TorchServe and creating a model archive (.mar) file.

Note: The following steps can be done locally on your computer or on the EC2 instance itself (recommended). If you choose to create the .mar file locally, you will need to copy it to the instance using scp or similar mechanism.

# Install TorchServe and related utilities
conda install torchserve torch-model-archiver torch-workflow-archiver -c pytorch

# Create a folder to store the output
mkdir model_store

# Download the `.pth` "state dict" file from PyTorch's model zoo
wget https://download.pytorch.org/models/densenet161-8d451a50.pth

# Clone the TorchServe repo which contains usable examples of `model.py` and `index_to_name.json` for the DenseNet model
git clone https://github.com/pytorch/serve.git
Creating a Model Archive File
Now that we have our inputs, we can generate the model archive.

Note the flags in the following command:

model-name: How TorchServe refers to the model
version: Models can be versioned and multiple versions can be deployed at once
model-file: The file that initializes the model using the PyTorch nn.Module base class
serialized-file: The .pth file containing the parameters of the model
export-path: Where the .mar file is saved
handler: A TorchServe-specific transform step to handle input and produce output
A full list of pre-written handlers is available here
For models that do not conform to basic handler behaviors, you can write a custom handler. (We'll be doing this soon when we deploy a more advanced model.)
In this case we are expecting image files as input and classes as output.
extra-files: Handler-specific requirement that converts class indices to human-readable names.
torch-model-archiver --model-name densenet161 --version 1.0 --model-file ./serve/examples/image_classifier/densenet_161/model.py --serialized-file densenet161-8d451a50.pth --export-path model_store --handler image_classifier --extra-files ./serve/examples/image_classifier/index_to_name.json
Check the output in the model_store directory. If everything worked, you should now see a portable model archive.

If you created the .mar file locally, upload it to the EC2 instance using scp or your preferred alternative.
Installing Docker
The most dependable way of running TorchServe is to use the TorchServe Docker image (which includes Java 11 and other dependencies).

Install Docker on your instance (assuming you are not using the DL AMI). The following steps are taken from the the convenience script guide.

# for Ubuntu AMI
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# In the Amazon Linux AMI, you may need to use `sudo yum install docker -y`)
Running the Server
You have to start the Docker process before you can issue docker commands.

sudo systemctl start docker
Start a server that points traffic at our model archive. Note these flags:

The -p flag will map a port from within the container runtime to the EC2 instance's ports (8080 for the app and 8081 for the management API)
The -v flag maps a local directory (/model_store) from our host machine and makes it available inside the Docker container.
--model-store will tell the torchserve image where to find the .mar file.
sudo docker run --rm -it -p 8080:8080 -p 8081:8081 -v $PWD/model_store:/model_store pytorch/torchserve:latest torchserve --model-store /model_store
If all has gone well, our model server is now running.

Configuring the Model
Simply running the server does not automatically create endpoints for the model. To do that, we must configure the model.

You'll want to leave your server running and showing log messages, so open a new shell and ssh back into the EC2 instance.
From your new shell, configure the model by sending an http request to the server:

curl -X POST "http://localhost:8081/models?initial_workers=1&batch_size=4&url=densenet161.mar"
Running inference
At this point, we have functioning image classifier deployed to the web. Let's test it:

In a shell running on your inference server, download an image to test with. The following command will download an image of a kitten, and make a web request about it to the predictions endpoint exposed by TorchServe.

curl https://raw.githubusercontent.com/pytorch/serve/master/examples/image_classifier/kitten.jpg > kitten.jpg
curl http://localhost:8080/predictions/densenet161 -T kitten.jpg
If it's working, you should get in response something approximately like:

{
  "tabby": 0.46661895513534546,
  "tiger_cat": 0.46449047327041626,
  "Egyptian_cat": 0.06614057719707489,
  "lynx": 0.0012924452312290668,
  "plastic_bag": 0.00022909804829396307
}
Deploying CLIP with custom TorchServe handlers
In the workflow above, we explored the simple case for deploying PyTorch models:

Get the model definition, serialized "state dict" (.pth file), and any associated files
Create a .mar file that bundles the models, files and a handler into a named and versioned package
Run the TorchServe server and enable the model for inference
However, there are some models — particularly proprietary or pre-packaged models — that do not lend themselves to the workflow above. In these situations, TorchServe allows us to define custom handler files.

Let's deploy one such model, OpenAI's CLIP.

CLIP is a multi-modal model trained on images and text embeddings, and is capable of classifying images into arbitrary classes. Our exploratory use case will involve classifying images into "coffee", "toast", and "other" classes.

The CLIP API has some differences to watch out for:

CLIP provides more than merely the model architecture definition and the trained parameter settings. It also comes with a set of utilities and helper functions for interfacing with the model, including inference APIs.
CLIP is stored as an entire git repo, unlike Densenet which was defined in a single model.py file.
The .pt file is loaded by the CLIP library itself, in a way that TorchServe's prewritten image_classifier handler does not support. As a result, we will have to define a custom PyTorch handler for CLIP.
CLIP requires extra configuration to allow it to classify images into arbitrary classes as opposed to Densenet161's presets.
Choosing the right instance
Because CLIP is a much larger model than Densenet, completing this section will require an AWS instance with sufficient memory like t2.medium

Review the pricing for non-t2.micro instances
You will want to select an instance with 4 GiB of memory or more
Your server will not need to be running for more than an hour or two to complete this exercise.
Consider setting up an AWS Budget in the Billing Console to alert you, in case you forget to turn off your server.
Follow these instructions to upgrade your instance if necessary.
ssh back into your instance once the upgrade is complete.
Download the CLIP State File
Download the CLIP state file from within your EC2 instance:
wget https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt
Providing a Placeholder model.py File
By nature, the archiving tool has a required parameter where you to specify a Python file that defines your model. But in this case, since we're including the CLIP repo as a dependency, we won't actually make use of the model defined in that file. All the same, we have to provide something, so we're going to construct a placeholder model.py file, just to satisfy the requirement.

Run the following command to generate the file
cat << EOF > model.py
class Model:
    def __init__(self):
        pass
EOF
Creating a Custom Handler File
Now you can define a custom handler that allows PyTorch to interface with the CLIP model.

Use the handler.py file from the folder you downloaded, which contains the custom CLIP handler implementation.
Generate the Model Archive
torch-model-archiver --model-name clip_model --export-path model_store --version 1.0 --model-file model.py --extra-files ViT-B-32.pt --handler handler.py
If you need to rebuild an archive file, add the --force flag. This will allow torch-model-archiver to overwrite existing archives.

Create a custom Docker image
OpenAI's official CLIP implementation is not available on the Python Package Index (PyPI) and therefore pip will need to download the dependency from GitHub before installing it.

Torchserve's ability to install custom dependencies is currently opt-in and has some limitations, including not being able to download dependencies using git.

To work around this, we can create a custom Docker image by extending the pytorch/torchserve:latest image we used earlier.

Use the Dockerfile from the folder you downloaded, which contains the Docker configuration for the custom TorchServe image.
Create a configuration file for the custom Docker image
Before we use Docker to deploy our model archive, we will need to create a Torchserve configuration file.

By default, Torchserve manages running the server from within Docker. But since our new Dockerfile uses a custom command to start the server, we need this new file to define which URLs and ports to use.

Run the following command to create config.properties.
cat << EOF > config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
EOF
0.0.0.0 allows traffic from the EC2 instance to route to the internal address of the Docker container.

Now that we have explicitly mapped urls within the container, we can continue building and running the container:

Build the docker image (and don't miss the dot at the end!):
sudo docker build -t clip-torchserve:latest .
If the previous container is still running, shut it down to release the application's ports:
sudo docker ps will list running containers
sudo docker stop <container-id> will stop a container
Run the docker image and map the exposed ports to the ports on the instance:
sudo docker run -it -p 8080:8080 -p 8081:8081 -p 8082:8082 clip-torchserve
Registering and testing the CLIP model
Reminder: running torchserve does not register the model automatically.

In a new shell (you will have to reconnect to AWS using ssh), register the model using the following command:
curl -X POST "http://localhost:8081/models?initial_workers=1&batch_size=4&url=clip_model.mar"
If you run into any errors or the worker process within the Docker container fails unexpectedly, you may need to use a server with more memory.

If registration was successful, run inference by passing the model an image to classify.

You can download another image — try an image of a cup of coffee or a piece of toast — or use the kitten image you downloaded previously.

curl http://localhost:8080/predictions/clip_model -T kitten.jpg
The server should respond with probabilities of whether the image was of "coffee", "toast", or "other" like so:

Unknown component: json
Serving Multiple Models
Since the amended Dockerfile copied clip_model.mar and densenet161.mar, you should be able to provision both models at once and issue inference requests to both!

Alternatives
Note, deploying to EC2 is a common way to host inference servers (a.k.a. "job servers") but there are a plethora of other platforms, including Amazon's own SageMaker (example)

You are also free to write your own web server using a Python framework like Flask, wrapped around PyTorch inference code.

You did it
Key Takeaways
Model archives enable portable deployment. TorchServe's .mar files bundle model definitions, weights, and handlers into deployable packages that abstract away complexity for production systems.

Infrastructure matters for model size. DenseNet-161 runs on t2.micro instances while CLIP requires t2.medium or larger. Memory requirements scale dramatically with model complexity.

Custom handlers unlock complex models. Standard handlers work for simple classification, but models like CLIP need custom code to handle their specific APIs and multi-modal inputs.

Docker solves dependency hell. Custom images handle complex dependencies (like git-based packages) that standard deployment methods can't manage.

Multiple models can coexist. Single servers can host multiple model endpoints simultaneously, enabling A/B testing and gradual rollouts.

Real World Applications
Production image classification: Deploy computer vision models for content moderation, quality control, or automated tagging
Multi-modal search: Use CLIP-style models for searching images with text queries in e-commerce or media platforms
Edge deployment: Package models for deployment on edge devices or air-gapped environments
Model versioning: Roll out new model versions alongside existing ones for safe production updates
Microservices architecture: Expose ML models as HTTP APIs that integrate with existing web services
Follow-up Resources
TorchServe Documentation - Official deployment framework
AWS SageMaker - Managed ML deployment platform
Triton Inference Server - NVIDIA's multi-framework serving platform
BentoML - Alternative model serving framework
MLflow Model Registry - Model versioning and lifecycle management
Deep Learning with PyTorch – PyTorch on AWS
Troubleshooting Guide | PyTorch/Serve documentation
Triton Inference Server — Nvidia's alternative to TorchServe
