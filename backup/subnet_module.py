import pulumi_aws as aws
import pulumi

def create_subnets(
    vpc_id: pulumi.Input[str],
    subnet_type: str,
    count: int,
    cidrs: list,
    names: list,
    igw_id: pulumi.Input[str] = None,
    resource_prefix: str = "subnet"
):
    subnets = []
    associations = []
    route_table = None

    if subnet_type == "public":
        if not igw_id:
            raise ValueError("igw_id must be provided for public subnets")
        route_table = aws.ec2.RouteTable(
            resource_name=f"{resource_prefix}-public-rt",
            vpc_id=vpc_id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    gateway_id=igw_id
                )
            ],
            tags={"Name": f"{resource_prefix}-public-rt"}
        )
    else:
        # Internal route table (local only)
        route_table = aws.ec2.RouteTable(
            resource_name=f"{resource_prefix}-internal-rt",
            vpc_id=vpc_id,
            tags={"Name": f"{resource_prefix}-internal-rt"}
        )

    for i in range(count):
        subnet = aws.ec2.Subnet(
            resource_name=f"{resource_prefix}-{subnet_type}-{i+1}",
            vpc_id=vpc_id,
            cidr_block=cidrs[i] if i < len(cidrs) else None,
            tags={
                "Name": names[i] if i < len(names) else f"{resource_prefix}-{subnet_type}-{i+1}"
            }
        )
        subnets.append(subnet)
        assoc = aws.ec2.RouteTableAssociation(
            resource_name=f"{resource_prefix}-{subnet_type}-rt-assoc-{i+1}",
            subnet_id=subnet.id,
            route_table_id=route_table.id
        )
        associations.append(assoc)

    return subnets, route_table, associations
