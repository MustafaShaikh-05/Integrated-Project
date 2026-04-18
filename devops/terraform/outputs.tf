# Outputs after apply — public IP and convenience app URL.
output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.insurevision_ec2.public_ip
}

output "app_url" {
  description = "URL to access the app"
  value       = "http://${aws_instance.insurevision_ec2.public_ip}:8000"
}
