# __main__.py
import pulumi
import pulumi_aws as aws
from subnet_module import create_subnet_groups, create_nat_gateways
from vpc import create_vpc_and_igw

# Config variables
config = pulumi.Config()
vpc_name = config.require('vpcName')
vpc_cidr = config.require('vpcCidr')
region = aws.config.region

# Create the VPC and Internet Gateway using the vpc module
vpc, igw = create_vpc_and_igw(vpc_name, vpc_cidr)

# Get subnet configurations from the config
subnet_groups = config.get_object('subnetGroups') or []

# Process subnet groups based on routing profiles
public_subnet_groups = []
private_subnet_groups = []
isolated_subnet_groups = []

for group in subnet_groups:
    profile = group.get('routingProfile', 'isolated')
    if profile == 'public':
        public_subnet_groups.append(group)
    elif profile == 'private':
        private_subnet_groups.append(group)
    else:  # isolated
        isolated_subnet_groups.append(group)

# First create public subnets as we need them for NAT gateways
public_subnets = []
public_route_tables = []
public_associations = []

if public_subnet_groups:
    public_subnets, public_route_tables, public_associations = create_subnet_groups(
        vpc_id=vpc.id,
        region=region,
        subnet_groups=public_subnet_groups,
        igw_id=igw.id
    )

# Create NAT Gateways if we have private subnet groups
nat_gateways = []
if private_subnet_groups:
    # Check if we have specific NAT Gateway configuration
    nat_count = config.get_int('natGatewayCount') or 1
    
    # We need public subnets for NAT gateways
    if not public_subnets:
        raise pulumi.RunError("Public subnets are required to create NAT Gateways for private subnets")
    
    nat_gateways = create_nat_gateways(
        vpc_id=vpc.id,
        public_subnets=public_subnets,
        nat_count=nat_count,
        resource_prefix=vpc_name
    )

# Now create private subnets with NAT gateways
private_subnets = []
private_route_tables = []
private_associations = []

if private_subnet_groups:
    private_subnets, private_route_tables, private_associations = create_subnet_groups(
        vpc_id=vpc.id,
        region=region,
        subnet_groups=private_subnet_groups,
        nat_gateway_ids=[ng.id for ng in nat_gateways]
    )

# Finally create isolated subnets
isolated_subnets = []
isolated_route_tables = []
isolated_associations = []

if isolated_subnet_groups:
    isolated_subnets, isolated_route_tables, isolated_associations = create_subnet_groups(
        vpc_id=vpc.id,
        region=region,
        subnet_groups=isolated_subnet_groups
    )

# Combine all subnets, route tables and associations
all_subnets = public_subnets + private_subnets + isolated_subnets
all_route_tables = public_route_tables + private_route_tables + isolated_route_tables
all_associations = public_associations + private_associations + isolated_associations

# Export outputs
pulumi.export('vpc_id', vpc.id)
pulumi.export('internet_gateway_id', igw.id)
pulumi.export('subnet_ids', [s.id for s in all_subnets])
pulumi.export('route_table_ids', [rt.id for rt in all_route_tables])
pulumi.export('route_table_associations', [assoc.id for assoc in all_associations])
pulumi.export('nat_gateway_ids', [ng.id for ng in nat_gateways])

# Export subnet counts by type
pulumi.export('public_subnet_count', len(public_subnets))
pulumi.export('private_subnet_count', len(private_subnets))
pulumi.export('isolated_subnet_count', len(isolated_subnets))
