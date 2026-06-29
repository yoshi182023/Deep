Key Takeaways
关键要点
1. MLOps as the Backbone of the ML Lifecycle
1. MLOps 作为机器学习生命周期的骨架
Big Picture: MLOps extends DevOps into machine learning, ensuring smooth transitions across data ingestion, model development, deployment, and monitoring.
全局视角：MLOps 将 DevOps 扩展到机器学习中，确保数据摄取、模型开发、部署与监控之间平滑衔接。
Why It Matters: Without structured handoffs and reproducible pipelines, models degrade quickly or fail to scale in production.
重要性：没有结构化交接和可复现流水线，模型会快速退化或无法在生产环境扩展。
Consider: How would your team’s productivity change if data, models, and deployment environments weren’t standardized?
思考：如果数据、模型和部署环境没有标准化，你的团队生产力会发生什么变化？
2. Data as the Starting Point
2. 数据是起点
Core Insight: Data ingestion, preparation, and feature engineering are prerequisites for meaningful modeling.
核心洞察：数据摄取、数据准备和特征工程是有效建模的前提。
How It Connects: Garbage in, garbage out — high-quality, version-controlled data underpins reliable models.
关联逻辑：垃圾进，垃圾出——高质量且有版本管理的数据是可靠模型的基础。
Practice: Use tools like Pachyderm (or simple folder structures with metadata) to keep track of dataset versions.
实践建议：使用 Pachyderm（或带元数据的简单文件夹结构）来追踪数据集版本。
So What?: Losing track of which dataset trained which model undermines reproducibility and governance.
所以呢：搞不清哪个数据集训练了哪个模型，会破坏可复现性和治理能力。
3. Experiment Tracking & Reproducibility
3. 实验跟踪与可复现性
Framework: Tools like Weights & Biases or Neptune AI log experiments, hyperparameters, and performance curves.
框架：Weights & Biases、Neptune AI 等工具可记录实验、超参数和性能曲线。
Reasoning Process: Unlike static code, ML models evolve through many iterations — history matters.
推理过程：与静态代码不同，ML 模型会经过多轮迭代演化——历史记录很重要。
Analogy: Think of experiment tracking as version control for scientific discovery, not just software.
类比：把实验跟踪看作科学发现的版本控制，而不只是软件版本控制。
Problem to Solve: How would you defend your model choices six months later without experiment logs?
待解决问题：如果没有实验日志，六个月后你如何为模型选择进行辩护？
4. Automation Through Orchestration Pipelines
4. 通过编排流水线实现自动化
Concept: Orchestration tools (Airflow, MLflow, Kubeflow, Metaflow, ZenML) automate workflows and enforce consistency.
概念：编排工具（Airflow、MLflow、Kubeflow、Metaflow、ZenML）可自动化工作流并保证一致性。
Key Decision Point: Choose triggers (manual vs automatic) carefully, since retraining frequency balances cost with model freshness.
关键决策点：谨慎选择触发方式（手动/自动），因为重训练频率需要在成本与模型新鲜度之间平衡。
Pitfall: Failing to separate pipelines by environment (data, training, inference) leads to brittle systems.
常见陷阱：未按环境（数据、训练、推理）拆分流水线会导致系统脆弱。
Transferable Insight: Any repetitive process that requires reliability benefits from automation.
可迁移洞察：任何需要可靠性的重复流程都能从自动化中受益。
5. Deployment and Monitoring as Continuous Loops
5. 将部署与监控视为持续循环
Deployment Breakdown: Export → Registry → Deployment (e.g., TorchServe, Docker, EC2).
部署拆解：导出 → 注册中心 → 部署（例如 TorchServe、Docker、EC2）。
Monitoring Focus: Beyond latency and throughput, track model drift and data drift to detect performance decay.
监控重点：除了时延与吞吐，还要跟踪模型漂移和数据漂移，以发现性能衰减。
Generative Models Twist: Standard metrics often fail — user feedback loops (thumbs up/down) become critical.
生成式模型的变化点：标准指标常常失效——用户反馈闭环（点赞/点踩）变得关键。
So What?: Deployment isn’t an endpoint; it’s the beginning of continuous quality assurance.
所以呢：部署不是终点，而是持续质量保障的起点。
6. Governance, Checkpointing, and Compliance
6. 治理、检查点与合规
Checkpointing: Save serialized snapshots of models to resume training or recover from failures.
检查点：保存模型序列化快照，以便恢复训练或从故障中恢复。
Governance: Logging datasets and training processes is essential for audits (e.g., legal disputes about training data).
治理：记录数据集与训练流程对审计至关重要（例如训练数据相关法律争议）。
Practical Relevance: Without checkpoints, model recovery is costly. Without logs, compliance is impossible.
实际意义：没有检查点，模型恢复成本高；没有日志，合规几乎不可能。
7. Platforms and Advanced Considerations
7. 平台与进阶考量
Full-Service Platforms: Amazon SageMaker, Google Vertex, and AutoML provide end-to-end solutions for teams with varied expertise.
全托管平台：Amazon SageMaker、Google Vertex、AutoML 为不同能力层次的团队提供端到端方案。
Distributed Training: Tools like Ray enable parallelization across GPUs, crucial for large models.
分布式训练：Ray 等工具支持跨 GPU 并行，对大模型尤为关键。
Training Paradigms: Batch vs online training trade off stability vs adaptability.
训练范式：批量训练与在线训练是在稳定性与适应性之间做权衡。
Deployment Targets: Models may need to run in cloud APIs, mobile apps, or local inference — ONNX and CoreML bridge these.
部署目标：模型可能需要运行在云 API、移动应用或本地推理中——ONNX 与 CoreML 可起到桥接作用。
So What?: Platform choice and deployment strategy determine scalability and accessibility.
所以呢：平台选择与部署策略决定可扩展性与可达性。
8. From Notebooks to Production Pipelines
8. 从 Notebook 到生产流水线
Core Shift: Notebooks are great for exploration but fragile in production.
核心转变：Notebook 适合探索，但在生产环境中较脆弱。
Tooling: Systems like Kale help convert notebooks into Kubeflow pipelines.
工具支持：Kale 等系统可帮助将 Notebook 转换为 Kubeflow 流水线。
Misconception: Productionizing ML is just about “exporting code” — in reality, it’s about building reproducible, automated systems.
常见误解：把 ML 投入生产只是“导出代码”——实际上是构建可复现、自动化系统。
Deploying pre-trained models
部署预训练模型
Get started by clicking 'download' and moving the downloaded content into your main coursework folder. You'll need these files to complete the exercise.
点击“download”开始，并将下载内容移动到你的课程主文件夹中。完成本练习需要这些文件。

Objectives:
目标：

Delve into working with ML models by deploying two pre-trained models
通过部署两个预训练模型，深入实践 ML 模型部署
Note the workflow involved in downloading, packaging, and running models
了解下载、打包与运行模型的工作流程
Note the resources and hardware requirements of running small and large models
了解运行大小模型所需的资源与硬件要求
Context
背景
Note: This exercise has two sections:
注意：本练习分为两个部分：

Deploying Densenet-161 on an AWS EC2 instance
在 AWS EC2 实例上部署 Densenet-161
Deploying CLIP with custom TorchServe handlers
使用自定义 TorchServe handler 部署 CLIP
We will first deploy a pre-trained PyTorch model, the Densenet-161 image classifier, to an AWS EC2 instance. DenseNet161 can sort images into about 1000 pre-defined classes.
我们将先把预训练的 PyTorch 模型 Densenet-161 图像分类器部署到 AWS EC2 实例。DenseNet161 可将图像分类到约 1000 个预定义类别中。

Later in the exercise, we will upgrade our deployment to also use OpenAI's CLIP model which is much larger but also capable of classifying images into arbitrary classes.
在练习后半部分，我们将升级部署并使用 OpenAI 的 CLIP 模型，它规模更大且可分类到任意类别。

Deploying Densenet-161 on an AWS EC2 instance
在 AWS EC2 实例上部署 Densenet-161
We're going to use an AWS instance to host the inference server for a pretrained model. (We assume you've created an AWS account already during the Environment Setup process at the beginning of this course.) AWS products, including EC2, can be found in the "Services" menu, at the top of the AWS Management Console's EC2 dashboard page.
我们将使用 AWS 实例来托管预训练模型的推理服务器。（默认你已在课程开始的环境搭建环节创建了 AWS 账户。）包括 EC2 在内的 AWS 产品可在 AWS 控制台 EC2 仪表盘顶部的“Services”菜单中找到。

On that page, find the option to initiate the process of launching a new instance.
在该页面找到“启动新实例”的入口。

Give it a name like "Deep Atlas Coursework Server"
将实例命名为类似“Deep Atlas Coursework Server”
Choosing an Amazon Machine Instance Type
选择 Amazon 机器实例类型
In general, it's a good idea to use one of the Deep Learning AMI's, which are already very well configured for use with each of the major ML frameworks. Though they can't be used with the free tier, they're still pretty cheap. If you try to configure machines yoruself, there are countless ways to get your dev ops steps wrong, making every step harder.
通常建议使用 Deep Learning AMI，它们已为主流 ML 框架做好配置。虽然免费套餐不可用，但成本仍较低。如果你自行配置机器，很容易在 DevOps 步骤中出错，导致每一步都更困难。

Even so, in this exercise we're going to take the hard road, and configure the machine for ML ourselves. This will give us experience closer to the metal, which we'll need down the road anyway if we ever work with (or have to build!) complex ML Ops pipelines. Let's limit ourselves to the free tier and see where it gets us.
即便如此，本练习中我们会选择更难的路线，自己配置机器以支持 ML。这会让你获得更贴近底层的经验，未来若要使用（或构建）复杂 MLOps 流水线会很有帮助。我们先限制在免费套餐范围内进行尝试。

NOTE: In the future, we recommend you select the Deep Learning AMI (PyTorch 2.x) to keep your life simple, even though it requires more storage and hardware than the free-tier allows.
注意：未来我们建议你选择 Deep Learning AMI（PyTorch 2.x）以简化流程，尽管它需要比免费套餐更多的存储和硬件。

Choose one of the following Application/OS images (AMIs):
从以下应用/操作系统镜像（AMI）中选择一个：
Ubuntu (recommended)
Ubuntu（推荐）
Amazon Linux (should work!)
Amazon Linux（也可用）
Configuring Your Instance For Launch
配置实例并启动
For the instance type, a free-tier t2-micro will suffice (you may choose a different one; be mindful of the hourly rates)
实例类型方面，免费套餐的 t2-micro 足够（你也可以选其他类型，但注意按小时计费）。
The second portion of this exercise will present higher memory requirements. You will need a t2.medium or more.
本练习第二部分内存要求更高，你需要 t2.medium 或更高规格。
Create a new key-pair login if necessary and download the key-file to a secure location on your computer. Do NOT check this into git!
如有需要，创建新的密钥对登录并将密钥文件下载到本机安全位置。不要把它提交到 git！
In the Network Settings, allow SSH, HTTP, and HTTPS traffic to your server (SSH for administration, and HTTP/S for inference tasks)
在网络设置中允许 SSH、HTTP 和 HTTPS 流量（SSH 用于管理，HTTP/S 用于推理请求）。
Choose the maximum amount of storage available in the free tier (30GB) or more if it's required by your AMI (~45GB for the DL AMI)
选择免费套餐可用的最大存储（30GB），若 AMI 需要则配置更多（DL AMI 约需 45GB）。
Click "Launch Instance", and connect to it from your local terminal
点击“Launch Instance”，然后在本地终端连接该实例。
In the dashboard's sidebar, navigate to Instances (section) > Instances (menu item) > [click on the instance ID, a link] > Connect > "SSH client" tab
在仪表盘侧边栏进入 Instances（分区）> Instances（菜单项）> [点击实例 ID 链接] > Connect > “SSH client” 标签页。
Follow Amazon's instructions for connecting
按 Amazon 提供的说明完成连接。
Setting Up Your Newly Launched Image
配置新启动的镜像环境
Installing Conda
安装 Conda
NOTE: You only need to install Conda if you are on the free-tier, and did not use a Deep Learning AMI
注意：只有在使用免费套餐且未使用 Deep Learning AMI 时，才需要安装 Conda。

Install conda, which is an alternative to pip preferred by the PyTorch ecosystem. The second command will offer a series of interactive prompts. In that process, you can accept the defaults, except for one:
安装 conda，它是 PyTorch 生态常用且可替代 pip 的工具。第二条命令会出现一系列交互提示，除一项外其余可使用默认值。

Select "yes" when prompted to activate conda automatically after starting a shell (otherwise, you will have to run conda activate every time you ssh into your instance).
当提示是否在 shell 启动后自动激活 conda 时，选择“yes”（否则每次 ssh 登录都要手动执行 conda activate）。
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh Miniconda3-latest-Linux-x86_64.sh
Per the onscreen instructions, you will need to close and reopen your shell to activate conda.
根据屏幕提示，你需要关闭并重新打开 shell 才能激活 conda。

type exit
use the same ssh command to re-connect to your ec2 instance (you may be able to press the 'up' key to recall that command).
使用相同的 ssh 命令重新连接 EC2 实例（可以按“上方向键”调出该命令）。
You can then verify that conda is working by running conda --version.
然后运行 conda --version 验证 conda 是否可用。
Installing Dependencies with Conda
使用 Conda 安装依赖
The dependencies we are using — particularly PyTorch — require Python 3.11. Linux ships with Python 3.12 by default. Conda will allow us to downgrade:
我们使用的依赖（尤其是 PyTorch）需要 Python 3.11，而 Linux 默认是 Python 3.12。Conda 可用于降级：

conda install python=3.11
Now we need to install PyTorch and its related libraries:
现在需要安装 PyTorch 及其相关库：

conda install pytorch torchvision torchaudio cpuonly -c pytorch
TorchServe and Model Archive Files
TorchServe 与模型归档文件
TorchServe is a library that can expose PyTorch models via a web server, with automatically generated API, logging, metrics, and model versioning capabilities.
TorchServe 是一个可通过 Web 服务暴露 PyTorch 模型的库，具备自动生成 API、日志、指标和模型版本管理能力。

To do this, you must first get TorchServe to create a model archive file for your target model, in the state you want to run it. A model archive file is a compressed representation of a trained model, ready to be run on an inference server. Having one allows you to treat the trained model as a well-functioning black box of prediction. Without it, you would have to manually load up the model architecture from the original source files that defined it, then load the parameters into an instance of that model architecture object.
为此，你需要先让 TorchServe 为目标模型生成一个可运行状态的模型归档文件。模型归档文件是训练模型的压缩表示，可直接在推理服务器运行。有了它，你可以把训练好的模型当作可用的预测黑盒；否则你需要手动从源文件加载模型结构，再把参数加载到该模型实例中。

In the simplest case, creating a model archive requires 3 inputs:
最简单情况下，创建模型归档需要 3 个输入：

A model definition (a Python model.py file that defines the model class)
模型定义（定义模型类的 Python model.py 文件）
A model's "state dict" (a .pth or .pt file that contains all the parameters of a model, saved separately)
模型的 “state dict”（.pth 或 .pt 文件，包含并单独保存模型全部参数）
A index_to_name JSON file which maps the index of the model's output to a human-readable label. With it, instead of seeing which indices correspond to the highest probabilities, we can see label names.
index_to_name JSON 文件，用于将模型输出索引映射为可读标签。有了它，你看到的是标签名而不是高概率索引号。
Set Up the Inputs to the Model Archiving Process
准备模型归档流程所需输入
Let's start by installing TorchServe and creating a model archive (.mar) file.
先安装 TorchServe 并创建模型归档（.mar）文件。

Note: The following steps can be done locally on your computer or on the EC2 instance itself (recommended). If you choose to create the .mar file locally, you will need to copy it to the instance using scp or similar mechanism.
注意：以下步骤可在本地电脑或 EC2 实例上执行（推荐在 EC2）。若在本地创建 .mar 文件，需要用 scp 或类似方式复制到实例。

# Install TorchServe and related utilities
conda install torchserve torch-model-archiver torch-workflow-archiver -c pytorch

# Create a folder to store the output
mkdir model_store

# Download the `.pth` "state dict" file from PyTorch's model zoo
wget https://download.pytorch.org/models/densenet161-8d451a50.pth

# Clone the TorchServe repo which contains usable examples of `model.py` and `index_to_name.json` for the DenseNet model
git clone https://github.com/pytorch/serve.git
Creating a Model Archive File
创建模型归档文件
Now that we have our inputs, we can generate the model archive.
现在输入已就绪，可以生成模型归档。

Note the flags in the following command:
注意以下命令中的参数：

model-name: How TorchServe refers to the model
model-name：TorchServe 中模型的名称
version: Models can be versioned and multiple versions can be deployed at once
version：模型可进行版本管理，并可同时部署多个版本
model-file: The file that initializes the model using the PyTorch nn.Module base class
model-file：使用 PyTorch nn.Module 基类初始化模型的文件
serialized-file: The .pth file containing the parameters of the model
serialized-file：包含模型参数的 .pth 文件
export-path: Where the .mar file is saved
export-path：.mar 文件保存位置
handler: A TorchServe-specific transform step to handle input and produce output
handler：TorchServe 特有的处理步骤，用于处理输入并生成输出
A full list of pre-written handlers is available here
预置 handler 的完整列表见此处
For models that do not conform to basic handler behaviors, you can write a custom handler. (We'll be doing this soon when we deploy a more advanced model.)
若模型不符合基础 handler 行为，可自行编写自定义 handler。（部署更高级模型时会用到。）
In this case we are expecting image files as input and classes as output.
此处我们期望输入是图像文件，输出是类别。
extra-files: Handler-specific requirement that converts class indices to human-readable names.
extra-files：handler 的额外要求，用于将类别索引转换成人类可读名称。
torch-model-archiver --model-name densenet161 --version 1.0 --model-file ./serve/examples/image_classifier/densenet_161/model.py --serialized-file densenet161-8d451a50.pth --export-path model_store --handler image_classifier --extra-files ./serve/examples/image_classifier/index_to_name.json
Check the output in the model_store directory. If everything worked, you should now see a portable model archive.
检查 model_store 目录输出。如果一切正常，你应能看到可移植的模型归档文件。

If you created the .mar file locally, upload it to the EC2 instance using scp or your preferred alternative.
如果你在本地创建了 .mar 文件，请使用 scp 或你偏好的方式上传到 EC2 实例。
Installing Docker
安装 Docker
The most dependable way of running TorchServe is to use the TorchServe Docker image (which includes Java 11 and other dependencies).
运行 TorchServe 最可靠的方式是使用 TorchServe Docker 镜像（包含 Java 11 和其他依赖）。

Install Docker on your instance (assuming you are not using the DL AMI). The following steps are taken from the the convenience script guide.
在实例上安装 Docker（假设你未使用 DL AMI）。以下步骤摘自便捷脚本指南。

# for Ubuntu AMI
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# In the Amazon Linux AMI, you may need to use `sudo yum install docker -y`)
Running the Server
运行服务器
You have to start the Docker process before you can issue docker commands.
在执行 docker 命令前，必须先启动 Docker 进程。

sudo systemctl start docker
Start a server that points traffic at our model archive. Note these flags:
启动一个将流量导向模型归档的服务。注意以下参数：

The -p flag will map a port from within the container runtime to the EC2 instance's ports (8080 for the app and 8081 for the management API)
`-p` 参数将容器内端口映射到 EC2 实例端口（8080 为应用端口，8081 为管理 API 端口）。
The -v flag maps a local directory (/model_store) from our host machine and makes it available inside the Docker container.
`-v` 参数把宿主机本地目录（/model_store）映射到 Docker 容器内部。
--model-store will tell the torchserve image where to find the .mar file.
`--model-store` 用于告诉 torchserve 镜像 .mar 文件所在位置。
sudo docker run --rm -it -p 8080:8080 -p 8081:8081 -v $PWD/model_store:/model_store pytorch/torchserve:latest torchserve --model-store /model_store
If all has gone well, our model server is now running.
如果一切顺利，模型服务器已运行。

Configuring the Model
配置模型
Simply running the server does not automatically create endpoints for the model. To do that, we must configure the model.
仅运行服务器不会自动为模型创建端点。要实现这一点，必须配置模型。

You'll want to leave your server running and showing log messages, so open a new shell and ssh back into the EC2 instance.
请保持服务器运行并显示日志，因此请打开新 shell 并重新 ssh 登录 EC2 实例。
From your new shell, configure the model by sending an http request to the server:
在新 shell 中，通过向服务器发送 HTTP 请求来配置模型：

curl -X POST "http://localhost:8081/models?initial_workers=1&batch_size=4&url=densenet161.mar"
Running inference
执行推理
At this point, we have functioning image classifier deployed to the web. Let's test it:
到这里，我们已将可用的图像分类器部署到 Web。现在测试它：

In a shell running on your inference server, download an image to test with. The following command will download an image of a kitten, and make a web request about it to the predictions endpoint exposed by TorchServe.
在推理服务器的 shell 中下载测试图片。以下命令会下载一张小猫图片，并向 TorchServe 暴露的预测端点发起请求。

curl https://raw.githubusercontent.com/pytorch/serve/master/examples/image_classifier/kitten.jpg > kitten.jpg
curl http://localhost:8080/predictions/densenet161 -T kitten.jpg
If it's working, you should get in response something approximately like:
若运行正常，你会收到大致如下响应：

{
  "tabby": 0.46661895513534546,
  "tiger_cat": 0.46449047327041626,
  "Egyptian_cat": 0.06614057719707489,
  "lynx": 0.0012924452312290668,
  "plastic_bag": 0.00022909804829396307
}
Deploying CLIP with custom TorchServe handlers
使用自定义 TorchServe handler 部署 CLIP
In the workflow above, we explored the simple case for deploying PyTorch models:
在上述流程中，我们演示了部署 PyTorch 模型的简单场景：

Get the model definition, serialized "state dict" (.pth file), and any associated files
获取模型定义、序列化的 “state dict”（.pth 文件）及相关文件
Create a .mar file that bundles the models, files and a handler into a named and versioned package
创建 .mar 文件，将模型、文件和 handler 打包为带名称与版本的包
Run the TorchServe server and enable the model for inference
运行 TorchServe 服务并启用模型推理
However, there are some models — particularly proprietary or pre-packaged models — that do not lend themselves to the workflow above. In these situations, TorchServe allows us to define custom handler files.
但有些模型——尤其是私有或预打包模型——并不适用于上述流程。在这些情况下，TorchServe 允许我们定义自定义 handler 文件。

Let's deploy one such model, OpenAI's CLIP.
让我们部署这样一个模型：OpenAI 的 CLIP。

CLIP is a multi-modal model trained on images and text embeddings, and is capable of classifying images into arbitrary classes. Our exploratory use case will involve classifying images into "coffee", "toast", and "other" classes.
CLIP 是在图像与文本嵌入上训练的多模态模型，能够将图像分类到任意类别。我们的示例将图像分为“coffee”“toast”“other”三类。

The CLIP API has some differences to watch out for:
CLIP API 有一些需要注意的差异：

CLIP provides more than merely the model architecture definition and the trained parameter settings. It also comes with a set of utilities and helper functions for interfacing with the model, including inference APIs.
CLIP 不仅提供模型结构定义和训练参数，还附带一组与模型交互的工具与辅助函数，包括推理 API。
CLIP is stored as an entire git repo, unlike Densenet which was defined in a single model.py file.
CLIP 以完整 git 仓库形式提供，不像 Densenet 只在单个 model.py 文件中定义。
The .pt file is loaded by the CLIP library itself, in a way that TorchServe's prewritten image_classifier handler does not support. As a result, we will have to define a custom PyTorch handler for CLIP.
`.pt` 文件由 CLIP 库自身加载，这种方式不受 TorchServe 预置 image_classifier handler 支持。因此我们必须为 CLIP 定义自定义 PyTorch handler。
CLIP requires extra configuration to allow it to classify images into arbitrary classes as opposed to Densenet161's presets.
与 Densenet161 预设类别不同，CLIP 需要额外配置才能支持任意类别分类。
Choosing the right instance
选择合适的实例
Because CLIP is a much larger model than Densenet, completing this section will require an AWS instance with sufficient memory like t2.medium
由于 CLIP 比 Densenet 大得多，完成本节需要内存充足的 AWS 实例，如 t2.medium。

Review the pricing for non-t2.micro instances
查看非 t2.micro 实例的价格
You will want to select an instance with 4 GiB of memory or more
建议选择内存 4 GiB 或以上的实例
Your server will not need to be running for more than an hour or two to complete this exercise.
完成本练习时，服务器通常无需连续运行超过一到两小时。
Consider setting up an AWS Budget in the Billing Console to alert you, in case you forget to turn off your server.
建议在 Billing Console 中设置 AWS Budget 提醒，防止忘记关闭服务器。
Follow these instructions to upgrade your instance if necessary.
如有需要，请按这些说明升级实例。
ssh back into your instance once the upgrade is complete.
升级完成后，重新 ssh 登录你的实例。
Download the CLIP State File
下载 CLIP 状态文件
Download the CLIP state file from within your EC2 instance:
在你的 EC2 实例中下载 CLIP 状态文件：
wget https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt
Providing a Placeholder model.py File
提供占位的 model.py 文件
By nature, the archiving tool has a required parameter where you to specify a Python file that defines your model. But in this case, since we're including the CLIP repo as a dependency, we won't actually make use of the model defined in that file. All the same, we have to provide something, so we're going to construct a placeholder model.py file, just to satisfy the requirement.
归档工具要求必须指定一个定义模型的 Python 文件参数。但在这里，由于我们将 CLIP 仓库作为依赖引入，不会实际使用该文件中定义的模型。即便如此，我们仍需提供一个文件，因此将创建一个占位的 model.py 来满足要求。

Run the following command to generate the file
运行以下命令生成该文件
cat << EOF > model.py
class Model:
    def __init__(self):
        pass
EOF
Creating a Custom Handler File
创建自定义 Handler 文件
Now you can define a custom handler that allows PyTorch to interface with the CLIP model.
现在你可以定义一个自定义 handler，使 PyTorch 能够与 CLIP 模型对接。

Use the handler.py file from the folder you downloaded, which contains the custom CLIP handler implementation.
使用你下载文件夹中的 handler.py 文件，其中包含自定义 CLIP handler 的实现。
Generate the Model Archive
生成模型归档文件
torch-model-archiver --model-name clip_model --export-path model_store --version 1.0 --model-file model.py --extra-files ViT-B-32.pt --handler handler.py
If you need to rebuild an archive file, add the --force flag. This will allow torch-model-archiver to overwrite existing archives.
如果你需要重新构建归档文件，请添加 --force 参数。这样可以让 torch-model-archiver 覆盖已有归档。

Create a custom Docker image
创建自定义 Docker 镜像
OpenAI's official CLIP implementation is not available on the Python Package Index (PyPI) and therefore pip will need to download the dependency from GitHub before installing it.
OpenAI 官方的 CLIP 实现不在 Python Package Index（PyPI）上，因此 pip 需要先从 GitHub 下载该依赖再进行安装。

Torchserve's ability to install custom dependencies is currently opt-in and has some limitations, including not being able to download dependencies using git.
TorchServe 安装自定义依赖的能力目前是可选启用的，并且存在一些限制，包括无法通过 git 下载依赖。

To work around this, we can create a custom Docker image by extending the pytorch/torchserve:latest image we used earlier.
为了解决这个问题，我们可以基于之前使用的 pytorch/torchserve:latest 镜像构建一个自定义 Docker 镜像。

Use the Dockerfile from the folder you downloaded, which contains the Docker configuration for the custom TorchServe image.
使用你下载文件夹中的 Dockerfile，其中包含自定义 TorchServe 镜像的 Docker 配置。
Create a configuration file for the custom Docker image
为自定义 Docker 镜像创建配置文件
Before we use Docker to deploy our model archive, we will need to create a Torchserve configuration file.
在使用 Docker 部署模型归档之前，我们需要先创建一个 TorchServe 配置文件。

By default, Torchserve manages running the server from within Docker. But since our new Dockerfile uses a custom command to start the server, we need this new file to define which URLs and ports to use.
默认情况下，TorchServe 会在 Docker 内管理服务器运行。但由于新的 Dockerfile 使用了自定义启动命令，我们需要这个新文件来定义要使用的 URL 和端口。

Run the following command to create config.properties.
运行以下命令创建 config.properties。
cat << EOF > config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
EOF
0.0.0.0 allows traffic from the EC2 instance to route to the internal address of the Docker container.
0.0.0.0 允许来自 EC2 实例的流量路由到 Docker 容器内部地址。

Now that we have explicitly mapped urls within the container, we can continue building and running the container:
现在我们已经显式映射了容器内的 URL，可以继续构建并运行容器：

Build the docker image (and don't miss the dot at the end!):
构建 Docker 镜像（别漏掉结尾的点！）：
sudo docker build -t clip-torchserve:latest .
If the previous container is still running, shut it down to release the application's ports:
如果前一个容器仍在运行，请将其关闭以释放应用端口：
sudo docker ps will list running containers
sudo docker stop <container-id> will stop a container
Run the docker image and map the exposed ports to the ports on the instance:
运行 Docker 镜像并将暴露端口映射到实例端口：
sudo docker run -it -p 8080:8080 -p 8081:8081 -p 8082:8082 clip-torchserve
Registering and testing the CLIP model
注册并测试 CLIP 模型
Reminder: running torchserve does not register the model automatically.
提醒：运行 torchserve 不会自动注册模型。

In a new shell (you will have to reconnect to AWS using ssh), register the model using the following command:
在新 shell 中（你需要通过 ssh 重新连接 AWS），使用以下命令注册模型：
curl -X POST "http://localhost:8081/models?initial_workers=1&batch_size=4&url=clip_model.mar"
If you run into any errors or the worker process within the Docker container fails unexpectedly, you may need to use a server with more memory.
如果你遇到错误，或 Docker 容器中的 worker 进程意外失败，可能需要使用内存更大的服务器。

If registration was successful, run inference by passing the model an image to classify.
如果注册成功，传入一张要分类的图片进行推理。

You can download another image — try an image of a cup of coffee or a piece of toast — or use the kitten image you downloaded previously.
你可以再下载一张图片——比如咖啡杯或吐司——也可以使用你之前下载的小猫图片。

curl http://localhost:8080/predictions/clip_model -T kitten.jpg
The server should respond with probabilities of whether the image was of "coffee", "toast", or "other" like so:
服务器应返回图片属于“coffee”“toast”或“other”的概率，类似如下：

Unknown component: json
未知组件：json
Serving Multiple Models
提供多个模型服务
Since the amended Dockerfile copied clip_model.mar and densenet161.mar, you should be able to provision both models at once and issue inference requests to both!
由于修改后的 Dockerfile 复制了 clip_model.mar 和 densenet161.mar，你应该能够一次部署两个模型并分别发起推理请求！

Alternatives
其他方案
Note, deploying to EC2 is a common way to host inference servers (a.k.a. "job servers") but there are a plethora of other platforms, including Amazon's own SageMaker (example)
注意，将服务部署到 EC2 是托管推理服务器（也称“作业服务器”）的常见方式，但还有许多其他平台，包括亚马逊自家的 SageMaker（示例）。

You are also free to write your own web server using a Python framework like Flask, wrapped around PyTorch inference code.
你也可以使用 Flask 等 Python 框架自行编写 Web 服务，并封装 PyTorch 推理代码。

You did it
你完成了
Key Takeaways
关键要点
Model archives enable portable deployment. TorchServe's .mar files bundle model definitions, weights, and handlers into deployable packages that abstract away complexity for production systems.
模型归档让部署可移植。TorchServe 的 .mar 文件将模型定义、权重和 handler 打包成可部署包，屏蔽了生产系统中的复杂性。

Infrastructure matters for model size. DenseNet-161 runs on t2.micro instances while CLIP requires t2.medium or larger. Memory requirements scale dramatically with model complexity.
基础设施与模型大小密切相关。DenseNet-161 可在 t2.micro 上运行，而 CLIP 需要 t2.medium 或更高配置。内存需求会随模型复杂度显著增长。

Custom handlers unlock complex models. Standard handlers work for simple classification, but models like CLIP need custom code to handle their specific APIs and multi-modal inputs.
自定义 handler 可支持复杂模型。标准 handler 适用于简单分类，但像 CLIP 这样的模型需要自定义代码来处理特定 API 和多模态输入。

Docker solves dependency hell. Custom images handle complex dependencies (like git-based packages) that standard deployment methods can't manage.
Docker 可解决依赖地狱。自定义镜像可以处理标准部署方式无法管理的复杂依赖（例如基于 git 的包）。

Multiple models can coexist. Single servers can host multiple model endpoints simultaneously, enabling A/B testing and gradual rollouts.
多个模型可以共存。单台服务器可同时托管多个模型端点，支持 A/B 测试和渐进式发布。

Real World Applications
真实世界应用
Production image classification: Deploy computer vision models for content moderation, quality control, or automated tagging
生产级图像分类：部署计算机视觉模型用于内容审核、质量控制或自动打标
Multi-modal search: Use CLIP-style models for searching images with text queries in e-commerce or media platforms
多模态搜索：在电商或媒体平台中使用 CLIP 类模型，通过文本查询搜索图像
Edge deployment: Package models for deployment on edge devices or air-gapped environments
边缘部署：将模型打包部署到边缘设备或隔离网络环境
Model versioning: Roll out new model versions alongside existing ones for safe production updates
模型版本管理：在现有版本旁逐步发布新版本，实现安全生产更新
Microservices architecture: Expose ML models as HTTP APIs that integrate with existing web services
微服务架构：将机器学习模型以 HTTP API 形式暴露，并与现有 Web 服务集成
Follow-up Resources
后续资源
TorchServe Documentation - Official deployment framework
TorchServe 文档 - 官方部署框架
AWS SageMaker - Managed ML deployment platform
AWS SageMaker - 托管式机器学习部署平台
Triton Inference Server - NVIDIA's multi-framework serving platform
Triton Inference Server - NVIDIA 的多框架推理服务平台
BentoML - Alternative model serving framework
BentoML - 替代性的模型服务框架
MLflow Model Registry - Model versioning and lifecycle management
MLflow Model Registry - 模型版本与生命周期管理
Deep Learning with PyTorch – PyTorch on AWS
Deep Learning with PyTorch – AWS 上的 PyTorch
Troubleshooting Guide | PyTorch/Serve documentation
故障排查指南 | PyTorch/Serve 文档
Triton Inference Server — Nvidia's alternative to TorchServe
Triton Inference Server — Nvidia 的 TorchServe 替代方案
