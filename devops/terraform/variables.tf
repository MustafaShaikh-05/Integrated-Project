# Input variables for the InsureVision AI Terraform stack.
variable "aws_region" {
  default = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 AMI for us-east-1"
  default     = "ami-0c7217cdde317cfec"
}

variable "key_name" {
  description = "AWS-KEY-VALUE PAIR"
  default     = "integrated-project-key"
}

variable "groq_api_key" {
  description = "Groq API key injected into EC2 user_data as .env (sensitive)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "instance_type" {
  description = "EC2 free tier instance type"
  default     = "t3.micro"
}
