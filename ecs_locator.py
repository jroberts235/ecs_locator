#! /usr/bin/env python3

import sys
import boto3
from pprint import pprint

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

    response = ecs_client.list_tasks(
        cluster=cluster_name,
        serviceName=service_name,
        desiredStatus='RUNNING',
    )

    response = ecs_client.describe_services(
        cluster=cluster_name,
        services=[
            service_name,
        ],
        include=[
            'TAGS',
        ]
    )

    try:
        task_def = response['services'][0]['taskDefinition']
    except IndexError:
        print(f'Error: { service_name } not found in { cluster_name } cluster!\n')
        exit(1)
    else:
        response = ecs_client.describe_task_definition(
            taskDefinition=task_def,
            include=[
                'TAGS',
            ]
        )

    try:
        port = response['taskDefinition']['containerDefinitions'][0]['portMappings'][0]['containerPort']
    except IndexError:
        port = 'none'

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

        try:
            container_arn = response['tasks'][0]['containerInstanceArn']
        except IndexError:
            print(f'Error: "container_arn" not found for { task_arn } on { cluster_name } cluster!\n')
            exit(1)
        else:
            response = ecs_client.describe_container_instances(
                cluster=cluster_name,
                containerInstances=[
                    container_arn,
                ],
                include=[
                    'TAGS',
                ]
            )

        try:
            ec2_id = response['containerInstances'][0]['ec2InstanceId']
        except IndexError:
            print(f'Error: "ec2_id" not found running { container_arn } on { cluster_name } cluster!\n')
            exit(1)
        else:

            response = ec2_client.describe_instances(
                InstanceIds=[
                    ec2_id,
                ],
            )

            id = ec2_id
            all_priv_ints = response['Reservations'][0]['Instances'][0]['NetworkInterfaces']
            first_int = response['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]
            public_ip = first_int['PrivateIpAddresses'][0]['Association']['PublicIp']
            private_ip = [interface['PrivateIpAddress'] for interface in all_priv_ints]
            public_name = first_int['PrivateIpAddresses'][0]['Association']['PublicDnsName']
            sg_id = first_int['Groups'][0]['GroupId']
            sg_name = first_int['Groups'][0]['GroupName']
            print(f'{last_status}\t{ id }\t{ public_ip }\t{ private_ip }\t{ public_name }\t{ port }\t{ sg_id }\t{ sg_name }')


if __name__ == '__main__':
    try:
        cluster_name = sys.argv[1]
    except IndexError:
        cluster_list()
    else:
        try:
            service_name = sys.argv[2]
        except IndexError:
            service_list(cluster_name=cluster_name)
        else:
            main(cluster_name=cluster_name, service_name=service_name)



