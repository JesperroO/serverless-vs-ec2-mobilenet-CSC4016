1.1 构建docker image：
docker build -t mobilenetv2-inference:v1.0-efs .


1.2 推送镜像到ECR：
$AccountId = "your_id"
$Region = "us-east-1"
$RepoName = "mobilenetv2"

# 登录ECR
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${Region}.amazonaws.com"

# 创建ECR仓库
aws ecr create-repository --repository-name $RepoName --region $Region

# 标记镜像
docker tag mobilenetv2-inference:v1.0-efs "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepoName}:v1.0-efs"

# 推送镜像
docker push "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepoName}:v1.0-efs"


2.1 创建EFS
在aws控制台中打开EFS服务，点击创建文件系统，确保使用和EC2相同的VPC,并记录系统id：fs-xxxxxxxxx

2.2 连接到EC2并安装必要组件：
sudo dnf install -y amazon-efs-utils docker awscli python3 python3-pip

sudo systemctl start docker
sudo systemctl enable docker

sudo usermod -a -G docker ec2-user

exit

#之后重新ssh连接到EC2

2.3 挂载EFS
# 创建挂载点目录
sudo mkdir -p /mnt/efs

# 挂载EFS（替换为你的文件系统ID）
sudo mount -t efs -o tls fs-03d6c6bb279b98ae7:/ /mnt/efs

# 验证挂载成功
df -h | grep efs

2.4 在EFS上安装Pytorch依赖：
# 创建目录结构
sudo mkdir -p /mnt/efs/site-packages /mnt/efs/cache/torch
sudo chmod -R 777 /mnt/efs

# 安装PyTorch到EFS
docker run --rm \
  -v /mnt/efs/site-packages:/efs-dependencies \
  -v /mnt/efs/cache/torch:/efs-dependencies/torch \
  -e TORCH_HOME=/efs-dependencies/torch \
  public.ecr.aws/docker/library/python:3.8-slim \
  bash -c "
    pip install --no-cache-dir --target /efs-dependencies \
    torch==1.9.0+cpu \
    torchvision==0.10.0+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html
  "

# 验证安装成功
ls -la /mnt/efs/site-packages/ | grep -E "torch|torchvision"

在后续新的EC2实例当中，通过以下方式实行EFS挂载：
# 步骤1: 安装基础软件（每个新实例都需要）
sudo dnf update -y
sudo dnf install -y amazon-efs-utils docker awscli python3 python3-pip
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user
# 重新登录

# 步骤2: 挂载现有的EFS（使用相同的文件系统ID）
sudo mkdir -p /mnt/efs
sudo mount -t efs -o tls fs-03d6c6bb279b98ae7:/ /mnt/efs

# 步骤3: 验证PyTorch依赖已存在
ls -la /mnt/efs/site-packages/torch*
# 应该能看到torch目录，无需重新安装

# 步骤4: 拉取和运行容器 - 关键修正：添加模型缓存目录挂载
docker run -d -p 5000:5000 \
  -v /mnt/efs/site-packages:/efs-dependencies \
  -v /mnt/efs/cache/torch:/efs-dependencies/torch \
  767397689428.dkr.ecr.us-east-1.amazonaws.com/mobilenetv2-inference:v1.0-efs

# 步骤5: 验证服务运行
curl http://localhost:5000/health