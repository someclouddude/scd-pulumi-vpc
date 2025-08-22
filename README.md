# AWS VPC Infrastructure with Pulumi

A comprehensive Pulumi project for creating AWS VPC infrastructure with configurable subnets and routing profiles.

## TL;DR

This module provisions:
- A complete VPC with Internet Gateway
- Subnet groups with customizable names and CIDR blocks
- Three routing profiles (public, private, isolated)
- Individual route tables for each subnet
- NAT Gateways (for private subnets)
- Configurable via YAML stack configurations

## Prerequisites

- An AWS account with permissions to create VPC resources
- AWS credentials configured in your environment
- Python 3.12 or later
- Pulumi CLI installed and logged inBucket Pulumi Template

 A minimal Pulumi template for provisioning a single AWS S3 bucket using Python.

 ## Overview

 This template provisions an S3 bucket (`pulumi_aws.s3.BucketV2`) in your AWS account and exports its ID as an output. It’s an ideal starting point when:
  - You want to learn Pulumi with AWS in Python.
  - You need a barebones S3 bucket deployment to build upon.
  - You prefer a minimal template without extra dependencies.

 ## Prerequisites

 - An AWS account with permissions to create S3 buckets.
 - AWS credentials configured in your environment (for example via AWS CLI or environment variables).
 - Python 3.6 or later installed.
 - Pulumi CLI already installed and logged in.

## Infrastructure Components

### VPC Module

The VPC module (`vpc.py`) provides:
- Creation of a Virtual Private Cloud (VPC) with a specified CIDR block
- Internet Gateway attached to the VPC
- Custom naming for all resources

### Subnet Module

The subnet module (`subnet_module.py`) offers:
- Flexible subnet group creation with custom naming
- Support for three routing profiles:
  - **Public**: Subnets with routes to the Internet Gateway for outbound/inbound internet access
  - **Private**: Subnets with routes to NAT Gateways for outbound-only internet access
  - **Isolated**: Subnets with no internet access (local VPC routing only)
- Individual route tables for each subnet (not shared)
- Custom CIDR block assignment
- Availability Zone placement
- Automatic creation of appropriate routes based on profile

## Project Layout

```
├── __main__.py         # Main entry point that creates the infrastructure
├── vpc.py              # VPC and Internet Gateway creation module
├── subnet_module.py    # Subnet creation and configuration module
├── Pulumi.yaml         # Project metadata and configuration
├── Pulumi.dev.yaml     # Development environment configuration
├── Pulumi.stg.yaml     # Staging environment configuration
├── requirements.txt    # Python dependencies
└── .gitignore          # Git ignore configuration
```

## Current Environment Configurations

### Development Environment (dev)

The development environment is configured in `Pulumi.dev.yaml` with:
- Region: `us-east-1`
- VPC CIDR: `10.10.0.0/16`
- Three public subnets: `10.10.1.0/24`, `10.10.2.0/24`, `10.10.3.0/24`
- Three private subnets: `10.10.11.0/24`, `10.10.12.0/24`, `10.10.13.0/24`
- Three isolated subnets: `10.10.21.0/24`, `10.10.22.0/24`, `10.10.23.0/24`

### Staging Environment (stg)

The staging environment is configured in `Pulumi.stg.yaml` with:
- Region: `us-east-1`
- VPC CIDR: `10.20.0.0/16`
- Three public subnets: `10.20.1.0/24`, `10.20.2.0/24`, `10.20.3.0/24`
- Three isolated subnets: `10.20.21.0/24`, `10.20.22.0/24`, `10.20.23.0/24`

## Configuration Structure

Each environment is configured with the following structure:

```yaml
config:
  aws:region: us-east-1
  vpc:vpcName: dev-vpc
  vpc:vpcCidr: 10.10.0.0/16
  vpc:natGatewayCount: 1  # Optional: Number of NAT gateways to create
  vpc:subnetGroups:
    - subnetName: example-public
      subnetCount: 3
      routingProfile: public  # Options: public, private, isolated
      availabilityZones: ["a", "b", "c"]  # Optional: defaults to a, b, c
      subnetCidrs:
        - 10.10.1.0/24
        - 10.10.2.0/24
        - 10.10.3.0/24
```

## Technical Usage

### Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd scd-pulumi-vpc
   ```

2. Set up the Python virtual environment:
   ```bash
   ./setup_venv.sh
   source venv/bin/activate
   ```

3. Select a stack:
   ```bash
   pulumi stack select dev
   ```

4. Preview the changes:
   ```bash
   pulumi preview
   ```

5. Deploy the infrastructure:
   ```bash
   pulumi up
   ```

### Creating a New Stack

1. Create a new stack:
   ```bash
   pulumi stack init prod
   ```

2. Configure the stack:
   ```bash
   pulumi config set aws:region us-east-1
   pulumi config set vpc:vpcName prod-vpc
   pulumi config set vpc:vpcCidr 10.30.0.0/16
   ```

3. Configure subnet groups as a YAML file:
   ```bash
   cat > subnet-config.yaml << EOL
   subnetGroups:
     - subnetName: prod-public
       subnetCount: 3
       routingProfile: public
       subnetCidrs:
         - 10.30.1.0/24
         - 10.30.2.0/24
         - 10.30.3.0/24
     - subnetName: prod-private
       subnetCount: 3
       routingProfile: private
       subnetCidrs:
         - 10.30.11.0/24
         - 10.30.12.0/24
         - 10.30.13.0/24
     - subnetName: prod-isolated
       subnetCount: 3
       routingProfile: isolated
       subnetCidrs:
         - 10.30.21.0/24
         - 10.30.22.0/24
         - 10.30.23.0/24
   EOL
   pulumi config set --path vpc:subnetGroups --file subnet-config.yaml
   ```

### Outputs

Once deployed, the stack exports:
- `vpc_id`: ID of the created VPC
- `internet_gateway_id`: ID of the Internet Gateway
- `subnet_ids`: List of all subnet IDs
- `route_table_ids`: List of all route table IDs
- `route_table_associations`: List of all route table association IDs
- `nat_gateway_ids`: List of created NAT Gateway IDs
- `public_subnet_count`: Number of public subnets created
- `private_subnet_count`: Number of private subnets created
- `isolated_subnet_count`: Number of isolated subnets created

Retrieve outputs with:
```bash
pulumi stack output vpc_id
```

## Extending the Infrastructure

To add more resources or customize the existing ones:

1. Modify the subnet configuration in the appropriate stack YAML file
2. Add new modules or extend existing ones as needed
3. Update the `__main__.py` to use your new modules or configurations
4. Preview and deploy your changes

## Troubleshooting

If you encounter issues with the virtual environment:
```bash
./setup_venv.sh
```

For other issues, ensure:
- AWS credentials are properly configured
- Pulumi CLI is installed and logged in
- Required IAM permissions are granted to your AWS user