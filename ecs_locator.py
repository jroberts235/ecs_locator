#! /usr/bin/env python3

import sys
import boto3

ecs_client = boto3.client('ecs')
ec2_client = boto3.client('ec2')


def cluster_list():
    response = ecs_client.list_clusters(
        maxResults=100,
    )

    for resp in response['clusterArns']:
        print(resp.split('/')[1])


def service_list(cluster_name=None):
    response = ecs_client.list_services(
        cluster=cluster_name,
        maxResults=100,
    )

    for resp in response['serviceArns']:
        print(resp.split('/')[1])


def main(cluster_name=None, service_name=None):
    response = None
    try:
        response = ecs_client.list_tasks(
            cluster=cluster_name,
            serviceName=service_name,
            desiredStatus='RUNNING',
        )
    except ecs_client.exceptions.ServiceNotFoundException:
        print(f'Error: No service named "{ service_name }" not found in cluster: { cluster_name }')
        exit(1)
    except ecs_client.exceptions.ClusterNotFoundException:
        print(f'Error: Cluster name "{ cluster_name }" not found')
        exit(1)

    response = ecs_client.describe_services(
        cluster=cluster_name,
        services=[
            service_name,
        ],
        include=[
            'TAGS',
        ]
    )

    task_def = response['services'][0]['taskDefinition']

    response = ecs_client.describe_task_definition(
        taskDefinition=task_def,
        include=[
            'TAGS',
        ]
    )

    try:
        container_port = response['taskDefinition']['containerDefinitions'][0]['portMappings'][0]['containerPort']
    except IndexError:
        container_port = 'none'
    try:
        host_port = response['taskDefinition']['containerDefinitions'][0]['portMappings'][0]['hostPort']
    except IndexError:
        host_port = '0'

    response = ecs_client.list_tasks(
        cluster=cluster_name,
        serviceName=service_name,
        desiredStatus='RUNNING',
    )

    for task_arn in response['taskArns']:
        response = ecs_client.describe_tasks(
            cluster=cluster_name,
            tasks=[
                task_arn,
            ],
            include=[
                'TAGS',
            ]
        )

        last_status = response['tasks'][0]['lastStatus']
        container_arn = response['tasks'][0]['containerInstanceArn']

        response = ecs_client.describe_container_instances(
            cluster=cluster_name,
            containerInstances=[
                container_arn,
            ],
            include=[
                'TAGS',
            ]
        )

        ec2_id = response['containerInstances'][0]['ec2InstanceId']

        response = ec2_client.describe_instances(
            InstanceIds=[
                ec2_id,
            ],
        )

        all_private_interfaces = response['Reservations'][0]['Instances'][0]['NetworkInterfaces']
        first_interface = response['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]
        public_ip = first_interface['PrivateIpAddresses'][0]['Association']['PublicIp']
        private_ips = [interface['PrivateIpAddress'] for interface in all_private_interfaces]
        public_name = first_interface['PrivateIpAddresses'][0]['Association']['PublicDnsName']
        sg_id = first_interface['Groups'][0]['GroupId']
        sg_name = first_interface['Groups'][0]['GroupName']

        print(f'{last_status}\t{ ec2_id }\t{ public_ip }\t{ private_ips }\t{ public_name }\t'
              f'{ host_port }:{ container_port }\t{ sg_id }\t{ sg_name }')


if __name__ == '__main__':
    try:
        cluster_name = sys.argv[1]
    except IndexError:
        print()
        cluster_list()
        print()
    else:
        try:
            service_name = sys.argv[2]
        except IndexError:
            print()
            service_list(cluster_name=cluster_name)
            print()
        else:
            print()
            main(cluster_name=cluster_name, service_name=service_name)
            print()
