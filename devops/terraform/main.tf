# Terraform root module: provisions a small EC2 instance and security group for InsureVision AI.
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

# Security group allowing port 22 (SSH) and 8000 (app)
resource "aws_security_group" "insurevision_sg" {
  name        = "insurevision-sg"
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
}

# EC2 t2.micro instance (free tier eligible in many accounts)
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
