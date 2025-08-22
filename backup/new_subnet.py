import pulumi
import pulumi_aws as aws
from typing import List, Optional

def create_subnets(
    vpc_id: pulumi.Input[str],
    vpc_cidr: str,
    count: int,
    cidrs: List[str],
    names: List[str],
    routing_profiles: Optional[List[str]] = None,  # 'public', 'private', 'isolated'
    azs: Optional[List[str]] = None,
    igw_id: Optional[pulumi.Input[str]] = None,
    nat_gateway_ids: Optional[List[pulumi.Input[str]]] = None,
    resource_prefix: str = "subnet"
):
    """
    Creates subnets with individual route tables based on routing profile.
    - public: adds IGW route
    - private: adds NAT GW route
    - isolated: local only
    """
