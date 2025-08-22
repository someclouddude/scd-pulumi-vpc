import pulumi
import pulumi_aws as aws

def create_vpc_and_igw(vpc_name, vpc_cidr):
    vpc = aws.ec2.Vpc(
        resource_name=vpc_name,
        cidr_block=vpc_cidr,
        tags={
            'Name': vpc_name
        }
    )
    igw = aws.ec2.InternetGateway(
        resource_name=f"{vpc_name}-igw",
        vpc_id=vpc.id,
        tags={
            'Name': f"{vpc_name}-igw"
        }
    )
    return vpc, igw
