#!/bin/bash
# Runs on first boot of the EC2 instance (via Terraform templatefile).
# Installs Docker, clones the repo, writes .env with GROQ_API_KEY, builds and runs the app.
# NOTE: ${groq_api_key} is filled by Terraform — keep this file processed via templatefile().
apt-get update -y
apt-get install -y docker.io git

systemctl start docker
systemctl enable docker

git clone https://github.com/MustafaShaikh-05/Integrated-Project.git /app
cd /app

echo "GROQ_API_KEY=${groq_api_key}" > .env

sudo docker build -f devops/Dockerfile -t insurevision-ai:latest .
sudo docker run -d -p 8000:8000 --env-file .env insurevision-ai:latest
