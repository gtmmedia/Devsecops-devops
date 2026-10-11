data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  name = "${var.project_name}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  # 10.0.0.0/24, 10.0.1.0/24, ...
  public_subnets = [for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 8, i)]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------- network ---
# Public subnets only, and no NAT gateway. A NAT gateway costs roughly $33 a
# month by itself, which is a lot for a demo. The trade-off is that worker
# nodes get public IPs (still protected by security groups). A production setup
# would add private subnets and put the nodes there.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.16"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr

  azs            = local.azs
  public_subnets = local.public_subnets

  enable_nat_gateway      = false
  enable_dns_hostnames    = true
  enable_dns_support      = true
  map_public_ip_on_launch = true

  # Lets Kubernetes find these subnets when it creates public load balancers
  # (the ingress controller's NLB).
  public_subnet_tags = {
    "kubernetes.io/role/elb"                  = 1
    "kubernetes.io/cluster/${local.name}-eks" = "shared"
  }
}

# ------------------------------------------------------------------- EKS ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = "${local.name}-eks"
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  cluster_endpoint_public_access = true

  # Whoever runs `terraform apply` becomes cluster admin.
  enable_cluster_creator_admin_permissions = true

  access_entries = {
    for i, arn in var.admin_principal_arns : "admin-${i}" => {
      principal_arn = arn
      policy_associations = {
        admin = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  }

  cluster_addons = {
    vpc-cni = {
      most_recent    = true
      before_compute = true
    }
    kube-proxy = {
      most_recent = true
    }
    coredns = {
      most_recent = true
    }
    # Lets the PostgreSQL PersistentVolumeClaim create an EBS disk.
    aws-ebs-csi-driver = {
      most_recent = true
    }
    # HPA reads CPU usage from metrics-server. Without it, HPA shows <unknown>.
    metrics-server = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size

      # The EBS CSI driver runs on the nodes and uses the node role to create disks.
      iam_role_additional_policies = {
        ebs_csi = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
      }
    }
  }
}
