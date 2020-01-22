# ecs_locator

### Requirements python3, boto3
### AWS credentials need to be int ~/.aws/credentials

### Usage:

`python ecs_locator.py - list all ECS clusters.`

`python ecs_locator.py CLUSTERNAME - list all services on the cluster.`

`python ecs_locator.py CLUSTERNAME SERVICENAME - show details about the instance(s) that the service is running on.`
