import pulumi
import pulumi_aws as aws
from typing import Dict, List, Optional, Tuple


def expand_az_name(region: str, az_suffix: str) -> str:
    """
    Expands an availability zone suffix to its full name
    E.g. 'a' -> 'us-east-1a' (if region is 'us-east-1')
    """
    # Make sure the suffix doesn't already contain the region
    if region in az_suffix:
        return az_suffix
    
    # Otherwise append the suffix to the region
    return f"{region}{az_suffix}"


def create_subnet_groups(
    vpc_id: pulumi.Input[str],
    region: str,
    subnet_groups: List[Dict],
    igw_id: Optional[pulumi.Input[str]] = None,
    nat_gateway_ids: Optional[List[pulumi.Input[str]]] = None
) -> Tuple[List[aws.ec2.Subnet], List[aws.ec2.RouteTable], List[aws.ec2.RouteTableAssociation]]:
    """
    Creates subnet groups based on configuration
    
    Args:
        vpc_id: The VPC ID to create subnets in
        region: The AWS region
        subnet_groups: List of subnet group configurations
        igw_id: ID of the Internet Gateway for public subnets
        nat_gateway_ids: List of NAT Gateway IDs for private subnets
        
    Returns:
        Tuple of (subnets, route_tables, route_table_associations)
    """
    all_subnets = []
    all_route_tables = []
    all_associations = []
    
    nat_gw_index = 0
    
    for group in subnet_groups:
        name = group.get("subnetName", "subnet")
        count = group.get("subnetCount", 1)
        routing_profile = group.get("routingProfile", "isolated")
        subnet_cidrs = group.get("subnetCidrs", [])
        # If azs are specified in the group, use them; otherwise default to a, b, c
        azs = group.get("availabilityZones", ["a", "b", "c"])
        
        # Make sure we have enough AZs for the count
        while len(azs) < count:
            azs.extend(azs[:count-len(azs)])
        
        # Expand AZ names to full regional names
        expanded_azs = [expand_az_name(region, az) for az in azs[:count]]
        
        for i in range(count):
            # Get subnet CIDR or raise error if not enough CIDRs provided
            if i >= len(subnet_cidrs):
                raise ValueError(f"Not enough subnet CIDRs provided for group {name}. Expected {count}, got {len(subnet_cidrs)}")
            
            subnet_cidr = subnet_cidrs[i]
            subnet_name = f"{name}-{i+1}"
            
            # Ensure we're using the right AZ for this subnet
            az_index = i % len(expanded_azs)
            subnet_az = expanded_azs[az_index]
            
            # Create subnet
            subnet = aws.ec2.Subnet(
                resource_name=subnet_name,
                vpc_id=vpc_id,
                cidr_block=subnet_cidr,
                availability_zone=subnet_az,
                map_public_ip_on_launch=(routing_profile == "public"),
                tags={
                    "Name": subnet_name
                }
            )
            
            # Create route table based on routing profile
            rt_name = f"{subnet_name}-rt"
            
            if routing_profile == "public":
                if not igw_id:
                    raise ValueError("Internet Gateway ID (igw_id) is required for public subnets")
                
                route_table = aws.ec2.RouteTable(
                    resource_name=rt_name,
                    vpc_id=vpc_id,
                    tags={"Name": rt_name}
                )
                
                # Add default route to IGW
                aws.ec2.Route(
                    resource_name=f"{subnet_name}-igw-route",
                    route_table_id=route_table.id,
                    destination_cidr_block="0.0.0.0/0",
                    gateway_id=igw_id
                )
                
            elif routing_profile == "private":
                if not nat_gateway_ids or nat_gw_index >= len(nat_gateway_ids):
                    raise ValueError(f"NAT Gateway ID is required for private subnet {subnet_name} but none was provided")
                
                nat_gw_id = nat_gateway_ids[nat_gw_index]
                nat_gw_index += 1
                
                route_table = aws.ec2.RouteTable(
                    resource_name=rt_name,
                    vpc_id=vpc_id,
                    tags={"Name": rt_name}
                )
                
                # Add default route to NAT Gateway
                aws.ec2.Route(
                    resource_name=f"{subnet_name}-nat-route",
                    route_table_id=route_table.id,
                    destination_cidr_block="0.0.0.0/0",
                    nat_gateway_id=nat_gw_id
                )
                
            else:  # isolated - no external routes, local only
                route_table = aws.ec2.RouteTable(
                    resource_name=rt_name,
                    vpc_id=vpc_id,
                    tags={"Name": rt_name}
                )
            
            # Associate route table with subnet
            association = aws.ec2.RouteTableAssociation(
                resource_name=f"{subnet_name}-rt-assoc",
                subnet_id=subnet.id,
                route_table_id=route_table.id
            )
            
            # Add to result lists
            all_subnets.append(subnet)
            all_route_tables.append(route_table)
            all_associations.append(association)
    
    return all_subnets, all_route_tables, all_associations


def create_nat_gateways(
    vpc_id: pulumi.Input[str],
    public_subnets: List[aws.ec2.Subnet],
    nat_count: int = 1,
    resource_prefix: str = "nat"
) -> List[aws.ec2.NatGateway]:
    """
    Creates NAT Gateways in public subnets
    
    Args:
        vpc_id: The VPC ID
        public_subnets: List of public subnets to place NAT Gateways in
        nat_count: Number of NAT Gateways to create
        resource_prefix: Prefix for resource naming
        
    Returns:
        List of created NAT Gateways
    """
    if not public_subnets:
        raise ValueError("Public subnets are required for NAT Gateway creation")
    
    if nat_count > len(public_subnets):
        raise ValueError(f"Cannot create {nat_count} NAT Gateways with only {len(public_subnets)} public subnets")
    
    nat_gateways = []
    
    for i in range(nat_count):
        # Use modulo to cycle through subnets if nat_count > len(public_subnets)
        subnet_index = i % len(public_subnets)
        
        # Create Elastic IP for NAT Gateway
        eip = aws.ec2.Eip(
            resource_name=f"{resource_prefix}-eip-{i+1}",
            vpc=True,
            tags={
                "Name": f"{resource_prefix}-eip-{i+1}"
            }
        )
        
        # Create NAT Gateway
        nat_gw = aws.ec2.NatGateway(
            resource_name=f"{resource_prefix}-natgw-{i+1}",
            allocation_id=eip.id,
            subnet_id=public_subnets[subnet_index].id,
            tags={
                "Name": f"{resource_prefix}-natgw-{i+1}"
            }
        )
        
        nat_gateways.append(nat_gw)
    
    return nat_gateways
