# Outputs after apply — fixed Elastic IP and app URL.
output "public_ip" {
  description = "Fixed Elastic IP — never changes between deploys!"
  value       = aws_eip.insurevision_eip.public_ip
}

output "app_url" {
  description = "App URL — bookmark this, it never changes!"
  value       = "http://${aws_eip.insurevision_eip.public_ip}:8000"
}