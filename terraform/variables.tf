variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix for resource names."
  type        = string
  default     = "quickdesk"
}

variable "environment" {
  description = "Environment label used in names and tags."
  type        = string
  default     = "demo"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Check `aws eks describe-cluster-versions` for what is in standard support."
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "How many availability zones (and public subnets) to use. Minimum 2."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "EKS needs subnets in at least two availability zones."
  }
}

variable "node_instance_types" {
  description = "EC2 instance types for the worker node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Number of worker nodes to start with. Three t3.medium nodes leave room for the app plus the monitoring stack (t3.medium nodes only fit ~17 pods each)."
  type        = number
  default     = 3
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "admin_principal_arns" {
  description = "Extra IAM users/roles that get cluster-admin (for example the identity GitHub Actions deploys with). The identity that runs terraform apply is always admin."
  type        = list(string)
  default     = []
}
