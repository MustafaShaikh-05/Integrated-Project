# Terraform root module: provisions EC2, security group and Elastic IP for InsureVision AI.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Security group with name_prefix — auto deleted cleanly on destroy
resource "aws_security_group" "insurevision_sg" {
  name_prefix = "insurevision-sg-"
  description = "Allow SSH and app traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# EC2 instance
resource "aws_instance" "insurevision_ec2" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.insurevision_sg.id]
  user_data              = templatefile("${path.module}/user_data.sh", { groq_api_key = var.groq_api_key })

  tags = {
    Name = "InsureVision-AI"
  }
}

# Elastic IP — fixed permanent IP that never changes!
resource "aws_eip" "insurevision_eip" {
  instance = aws_instance.insurevision_ec2.id
  domain   = "vpc"

  tags = {
    Name = "InsureVision-AI-EIP"
  }
}