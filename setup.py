import boto3
import os
from string import Template

'''
MANUAL STEPS
    - Setup a wildcard certificate for *.company.co.in in AWS Certificate Manager and get the certificate arn.
'''

'''
SCRIPT VARIABLES
'''
COMPANY_NAME = 'docon'
HEVO_VPC_ID = 'vpc-25fe4042'
HEVO_AWS_ACCOUNT_ID = '475116478827'
HEVO_AWS_REGION = 'ap-southeast-1'
HEVO_VPC_CIDR = '10.0.0.0/16'
AWS_REGION = 'ap-south-1'
AWS_AVAILABILITY_ZONE = 'ap-south-1b'
ELB_CERT_ARN = 'arn:aws:acm:ap-south-1:691920331443:certificate/14af4a3d-6563-4f47-a278-483872683776'

IAM_ROLE_NAME = 'hevo-' + COMPANY_NAME + '-role'
IAM_POLICY_NAME = 'hevo-' + COMPANY_NAME + '-policy'
IAM_POLICY_TEMPLATE = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":["arn:aws:s3:::hevo-$COMPANY_NAME-consistency-module-athena-db","arn:aws:s3:::hevo-$COMPANY_NAME-consistency-module-athena-db/*","arn:aws:s3:::hevo-artifacts-prod","arn:aws:s3:::hevo-artifacts-prod/*","arn:aws:s3:::hevo-artifacts","arn:aws:s3:::hevo-artifacts/*","arn:aws:s3:::hevo-$COMPANY_NAME","arn:aws:s3:::hevo-$COMPANY_NAME/*"]},{"Effect":"Allow","Action":["athena:*"],"Resource":["*"]},{"Effect":"Allow","Action":["glue:CreateDatabase","glue:DeleteDatabase","glue:GetDatabase","glue:GetDatabases","glue:UpdateDatabase","glue:CreateTable","glue:DeleteTable","glue:BatchDeleteTable","glue:UpdateTable","glue:GetTable","glue:GetTables","glue:BatchCreatePartition","glue:CreatePartition","glue:DeletePartition","glue:BatchDeletePartition","glue:UpdatePartition","glue:GetPartition","glue:GetPartitions","glue:BatchGetPartition"],"Resource":["*"]},{"Effect":"Allow","Action":["elasticloadbalancing:*"],"Resource":["*"]},{"Effect":"Allow","Action":["elasticloadbalancing:DescribeLoadBalancers","elasticloadbalancing:DescribeTags","elasticloadbalancing:DescribeInstanceHealth","ec2:DescribeInstances","ec2:CreateTags","ec2:DeleteTags","ec2:DescribeTags"],"Resource":"*"}]}'  # noqa
IAM_POLICY = Template(IAM_POLICY_TEMPLATE).substitute({'COMPANY_NAME': COMPANY_NAME})
INSTANCE_PROFILE_NAME = 'hevo-' + COMPANY_NAME + '-instance-profile'

VPC_CIDR = '172.16.0.0/16'
KEY_PAIR = 'hevo-' + COMPANY_NAME + ''
VPC_NAME = 'hevo-' + COMPANY_NAME + '-vpc'
INTERNET_GATEWAY_NAME = 'hevo-' + COMPANY_NAME + '-ig'
VPC_SUBNET_NAME = 'hevo-' + COMPANY_NAME
VPC_SECURITY_GROUP_NAME = 'hevo-' + COMPANY_NAME + '-sg'
SUBNET_IPv4_CIDR = '172.16.2.0/24'
VPC_PEERING_CONNECTION_NAME = '' + COMPANY_NAME + '-hevo'

APP_NODES_NAME = '' + COMPANY_NAME + '-dev-service'
APP_NODES_AMI = 'ami-0e2eec6666c82a188'  # Hevo Base Image
APP_NODES_INSTANCE_TYPE = 'm5.large'
APP_NODES_COUNT = 3  # 3 EC2 Instances
APP_NODES_STORAGE_SIZE = 200  # 200GB

CACHE_NODES_NAME = '' + COMPANY_NAME + '-dev-cache'
CACHE_NODES_AMI = 'ami-0e2eec6666c82a188'
CACHE_NODES_INSTANCE_TYPE = 'm5.large'
CACHE_NODES_COUNT = 1  # 1 EC2 Instance
CACHE_NODES_STORAGE_SIZE = 50

CONSUL_NODES_NAME = '' + COMPANY_NAME + '-infra-consul'
CONSUL_NODES_AMI = 'ami-0e2eec6666c82a188'
CONSUL_NODES_INSTANCE_TYPE = 't2.nano'
CONSUL_NODES_COUNT = 1  # 1 EC2 Instance
CONSUL_NODES_STORAGE_SIZE = 8

DB_NODES_NAME = '' + COMPANY_NAME + '-infra-db'
DB_NODES_AMI = 'ami-0e2eec6666c82a188'
DB_NODES_INSTANCE_TYPE = 'c5.large'
DB_NODES_COUNT = 1  # 1 EC2 Instance
DB_NODES_STORAGE_SIZE = 60

S3_BUCKETS = ['hevo-' + COMPANY_NAME + '', 'hevo-' + COMPANY_NAME + '-consistency-module-athena-db']
ALLOWED_INGRESS_IN_SECUIRTY_GROUP_IP = '10.0.0.0/16'
ELB_NAME = 'hevo-' + COMPANY_NAME + '-elb'
'''
CLIENTS AND RESOURCES
'''
client = boto3.client('ec2')
ec2 = boto3.resource('ec2')
s3 = boto3.client('s3')
elb_client = boto3.client('elb')
iam_client = boto3.client('iam')


def get_iam_policy_arn():
    response = iam_client.list_policies(
        Scope='Local'
    )
    for policy in response['Policies']:
        if policy['PolicyName'] == IAM_POLICY_NAME:
            return policy['Arn']


def get_instance_profile_arn():
    response = iam_client.get_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
    return response['InstanceProfile']['Arn']


def create_policy():
    return iam_client.create_policy(
        PolicyName=IAM_POLICY_NAME,
        PolicyDocument=IAM_POLICY,
    )


def create_instance_profile():
    iam_client.create_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)


def add_role_to_instance_profile():
    iam_client.add_role_to_instance_profile(
        InstanceProfileName=INSTANCE_PROFILE_NAME,
        RoleName=IAM_ROLE_NAME
    )


def create_role():
    policy = create_policy()
    response = iam_client.create_role(
        RoleName=IAM_ROLE_NAME,
        AssumeRolePolicyDocument='{"Version":"2012-10-17","Statement":{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}}'
    )

    response = iam_client.attach_role_policy(
        RoleName=IAM_ROLE_NAME,
        PolicyArn=policy['Policy']['Arn']
    )
    return response


def create_key_pair():
    ec2.create_key_pair(KeyName=KEY_PAIR)


def create_vpc():
    vpc = client.create_vpc(
        CidrBlock=VPC_CIDR,
    )

    client.create_tags(
        Resources=[
            vpc['Vpc']['VpcId'],
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': VPC_NAME
            },
        ]
    )
    return vpc['Vpc']['VpcId']


def create_internet_gateway():
    internet_gateway = ec2.create_internet_gateway()
    client.create_tags(
        Resources=[
            internet_gateway.id,
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': INTERNET_GATEWAY_NAME
            },
        ]
    )
    return internet_gateway


def attach_internet_gateway(vpc, internet_gateway):
    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)


def create_subnet(vpc):
    subnet = vpc.create_subnet(
        AvailabilityZone=AWS_AVAILABILITY_ZONE,
        CidrBlock=SUBNET_IPv4_CIDR
    )
    client.create_tags(
        Resources=[
            subnet.subnet_id,
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': VPC_SUBNET_NAME
            },
        ]
    )
    client.modify_subnet_attribute(
        MapPublicIpOnLaunch={
            'Value': True
        },
        SubnetId=subnet.subnet_id
    )
    return subnet


def create_security_group(vpc):
    security_group = vpc.create_security_group(
        Description='Hevo security group for on-premise infrastructure',
        GroupName=VPC_SECURITY_GROUP_NAME
    )
    client.create_tags(
        Resources=[
            security_group.group_id,
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': VPC_SECURITY_GROUP_NAME
            },
        ]
    )
    return security_group


def create_nodes(subnet, security_group, NODES_STORAGE_SIZE, NODES_AMI, NODES_INSTANCE_TYPE, NODES_COUNT, NODES_NAME):
    ''' Create application nodes '''
    instances = ec2.create_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': NODES_STORAGE_SIZE,
                    'VolumeType': 'gp2'
                }
            },
        ],
        ImageId=NODES_AMI,
        InstanceType=NODES_INSTANCE_TYPE,
        MaxCount=NODES_COUNT,
        MinCount=NODES_COUNT,
        KeyName=KEY_PAIR,
        Placement={
            'AvailabilityZone': AWS_AVAILABILITY_ZONE,
        },
        Monitoring={
            'Enabled': True
        },
        SecurityGroupIds=[
            security_group.group_id,
        ],
        SubnetId=subnet.subnet_id,
        # TODO: Attach Instance Profile ARN later as it is not created immediately
        # IamInstanceProfile={
        #     "Name": IAM_ROLE_NAME
        # }
    )
    count = 1
    for instance in instances:
        client.create_tags(
            Resources=[
                instance.instance_id,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': NODES_NAME + '-' + str(count)
                },
            ]
        )
        count += 1
    return instances


def create_s3_buckets():
    for bucket in S3_BUCKETS:
        s3.create_bucket(
            ACL='private',
            Bucket=bucket,
            CreateBucketConfiguration={
                'LocationConstraint': AWS_REGION
            }
        )


def create_elb(subnet, security_group):
    elb = elb_client.create_load_balancer(
        LoadBalancerName=ELB_NAME,
        Listeners=[
            {
                'Protocol': 'HTTP',
                'LoadBalancerPort': 80,
                'InstanceProtocol': 'HTTP',
                'InstancePort': 80,
                'SSLCertificateId': ELB_CERT_ARN
            },
            {
                'Protocol': 'HTTPS',
                'LoadBalancerPort': 443,
                'InstanceProtocol': 'HTTPS',
                'InstancePort': 443,
                'SSLCertificateId': ELB_CERT_ARN
            },
        ],
        Subnets=[
            subnet.subnet_id,
        ],
        SecurityGroups=[
            security_group.group_id,
        ],
        Scheme='internet-facing',
        Tags=[
            {
                'Key': 'Name',
                'Value': ELB_NAME
            },
        ]
    )

    instances_list = []
    nodes = [APP_NODES_NAME + '-' + str(i) for i in range(1, APP_NODES_COUNT + 1)]
    instances = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': nodes}])
    for reservation in instances['Reservations']:
        instances = reservation['Instances']
        for instance in instances:
            id = instance['InstanceId']
            try:
                if instance['State']['Name'] != 'terminated':
                    instances_list.append({'InstanceId': id})
            except Exception as e:
                print (e)

    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=ELB_NAME,
        Instances=instances_list
    )
    return elb


def create_vpc_peering_connection(vpc_id):
    vpc_peering_connection = client.create_vpc_peering_connection(
        PeerOwnerId=HEVO_AWS_ACCOUNT_ID,
        PeerVpcId=HEVO_VPC_ID,
        VpcId=vpc_id,
        PeerRegion=HEVO_AWS_REGION
    )
    client.create_tags(
        Resources=[
            vpc_peering_connection['VpcPeeringConnection']['VpcPeeringConnectionId'],
        ],
        Tags=[
            {
                'Key': 'Name',
                'Value': VPC_PEERING_CONNECTION_NAME
            },
        ]
    )
    return vpc_peering_connection


def create_hevo_vpc_route_table_entry():
    client.create_route(
        DestinationCidrBlock=HEVO_VPC_CIDR,
        VpcPeeringConnectionId=get_vpc_peering_connection_id(),
        RouteTableId=get_vpc_route_table_id(),
    )


def create_route_table_entry():
    client.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=get_vpc_internet_gateway_id(),
        RouteTableId=get_vpc_route_table_id(),
    )


def add_rules_to_security_group(security_group):
    security_group = ec2.SecurityGroup(security_group.group_id)
    security_group.authorize_ingress(IpProtocol="tcp", CidrIp="0.0.0.0/0", FromPort=80, ToPort=80)
    security_group.authorize_ingress(IpProtocol="tcp", CidrIp="0.0.0.0/0", FromPort=443, ToPort=443)
    security_group.authorize_ingress(IpProtocol="-1", CidrIp=ALLOWED_INGRESS_IN_SECUIRTY_GROUP_IP)


def get_vpc_id():
    vpcs = client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [VPC_NAME]}])
    for vpc in vpcs['Vpcs']:
        return vpc['VpcId']


def get_vpc_route_table_id():
    response = client.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    get_vpc_id(),
                ]
            },
        ]
    )
    for route_table in response['RouteTables']:
        return route_table['RouteTableId']


def get_vpc_internet_gateway_id():
    igs = client.describe_internet_gateways(Filters=[{'Name': 'tag:Name', 'Values': [INTERNET_GATEWAY_NAME]}])
    for ig in igs['InternetGateways']:
        return ig['InternetGatewayId']


def get_vpc_peering_connection_id():
    vpc_peering_connections = client.describe_vpc_peering_connections(Filters=[{'Name': 'tag:Name', 'Values': [VPC_PEERING_CONNECTION_NAME]}])
    for vpc_peering_connection in vpc_peering_connections['VpcPeeringConnections']:
        return vpc_peering_connection['VpcPeeringConnectionId']


def delete_subnet():
    subnets = client.describe_subnets(Filters=[{'Name': 'tag:Name', 'Values': [VPC_SUBNET_NAME]}])
    for subnet in subnets['Subnets']:
        client.delete_subnet(SubnetId=subnet['SubnetId'])


def delete_security_group():
    security_groups = client.describe_security_groups(Filters=[{'Name': 'tag:Name', 'Values': [VPC_SECURITY_GROUP_NAME]}])
    for security_group in security_groups['SecurityGroups']:
        client.delete_security_group(GroupId=security_group['GroupId'])


def delete_nodes(NODES_NAME, NODES_COUNT):
    nodes = [NODES_NAME + '-' + str(i) for i in range(1, NODES_COUNT + 1)]
    instances = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': nodes}])
    for reservation in instances['Reservations']:
        instances = reservation['Instances']
        for instance in instances:
            id = instance['InstanceId']
            try:
                if instance['State']['Name'] != 'terminated':
                    client.modify_instance_attribute(InstanceId=id, DisableApiTermination={'Value': False})
                    client.terminate_instances(InstanceIds=[id])
            except Exception as e:
                print (e)


def delete_s3_buckets():
    try:
        for bucket_name in S3_BUCKETS:
            bucket = boto3.resource('s3').Bucket(bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
    except Exception as e:
        print (e)


def delete_vpc_peering_connection():
    client.delete_vpc_peering_connection(VpcPeeringConnectionId=get_vpc_peering_connection_id())


def delete_elb():
    response = elb_client.delete_load_balancer(
        LoadBalancerName=ELB_NAME
    )
    return response


def delete_internet_gateway():
    try:
        vpc_id = get_vpc_id()
        ig_id = get_vpc_internet_gateway_id()
        client.detach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
        client.delete_internet_gateway(InternetGatewayId=ig_id)
    except Exception as e:
        print (e)


def delete_vpc():
    vpcs = client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [VPC_NAME]}])
    for vpc in vpcs['Vpcs']:
        client.delete_vpc(VpcId=vpc['VpcId'])


def delete_key_pair():
    client.delete_key_pair(KeyName=KEY_PAIR)


def delete_role_policy():
    try:
        iam_client.delete_policy(PolicyArn=get_iam_policy_arn())
    except Exception as e:
        print (e)


def delete_role():
    try:
        iam_client.detach_role_policy(
            RoleName=IAM_ROLE_NAME,
            PolicyArn=get_iam_policy_arn()
        )
        iam_client.delete_role(RoleName=IAM_ROLE_NAME)
    except Exception as e:
        print (e)


def delete_instance_profile():
    try:
        iam_client.remove_role_from_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME,
            RoleName=IAM_ROLE_NAME
        )
    except Exception as e:
        print (e)
    try:
        iam_client.delete_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
    except Exception as e:
        print (e)


def instantiate():
    create_key_pair()
    vpc_id = create_vpc()
    vpc = ec2.Vpc(vpc_id)
    subnet = create_subnet(vpc)
    security_group = create_security_group(vpc)
    internet_gateway = create_internet_gateway()
    attach_internet_gateway(vpc, internet_gateway)
    add_rules_to_security_group(security_group)
    create_role()
    create_instance_profile()
    add_role_to_instance_profile()
    create_nodes(subnet, security_group, APP_NODES_STORAGE_SIZE, APP_NODES_AMI, APP_NODES_INSTANCE_TYPE, APP_NODES_COUNT, APP_NODES_NAME)
    create_nodes(subnet, security_group, CACHE_NODES_STORAGE_SIZE, CACHE_NODES_AMI, CACHE_NODES_INSTANCE_TYPE, CACHE_NODES_COUNT, CACHE_NODES_NAME)
    create_nodes(subnet, security_group, CONSUL_NODES_STORAGE_SIZE, CONSUL_NODES_AMI, CONSUL_NODES_INSTANCE_TYPE, CONSUL_NODES_COUNT, CONSUL_NODES_NAME)
    create_nodes(subnet, security_group, DB_NODES_STORAGE_SIZE, DB_NODES_AMI, DB_NODES_INSTANCE_TYPE, DB_NODES_COUNT, DB_NODES_NAME)
    create_vpc_peering_connection(vpc_id)
    create_route_table_entry()
    create_elb(subnet, security_group)
    create_s3_buckets()


def tear_down():
    delete_key_pair()
    delete_nodes(APP_NODES_NAME, APP_NODES_COUNT)
    delete_nodes(CACHE_NODES_NAME, CACHE_NODES_COUNT)
    delete_nodes(CONSUL_NODES_NAME, CONSUL_NODES_COUNT)
    delete_nodes(DB_NODES_NAME, DB_NODES_COUNT)
    delete_instance_profile()
    delete_role()
    delete_role_policy()
    delete_elb()
    delete_subnet()
    delete_security_group()
    delete_internet_gateway()
    delete_vpc_peering_connection()
    delete_vpc()
    delete_s3_buckets()


# Main menu
def main_menu():
    os.system('clear')
    print ("Welcome,\n")
    print ("Please choose the action you want to take:")
    print ("1. Instantiate AWS-Hevo Setup")
    print ("2. Tear-Down AWS-Hevo Setup")
    print ("3. Create Hevo VPC route table entry")
    print ("\n0. Quit")
    choice = raw_input(" >>  ")
    exec_menu(choice)

    return


# Menu definition
menu_actions = {
    'main_menu': main_menu,
    '1': instantiate,
    '2': tear_down,
    '3': create_hevo_vpc_route_table_entry,
    '0': exit,
}


# Execute menu
def exec_menu(choice):
    os.system('clear')
    ch = choice.lower()
    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print ("Invalid selection, please try again.\n")
            menu_actions['main_menu']()
    return


# Main Program
if __name__ == "__main__":
    main_menu()
