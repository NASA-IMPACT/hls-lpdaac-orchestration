from aws_cdk import (    
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_
)
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
import os

class ReconciliationtaskStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        reconciliationTaskRole = iam.Role(self, "reconciliationTask-taskRole-v2",role_name="reconciliationTask-taskRole-v2",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        iam.CfnManagedPolicy(self, "assumeGCCRolePolicy",
            managed_policy_name="assumeGCCRolePolicy",
            policy_document ={
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "AssumeRole",
                    "Effect": "Allow",
                    "Resource": "*",
                    "Action": "sts:AssumeRole",
                }]},
            roles=[reconciliationTaskRole.role_name])
        
        reconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies1",managed_policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess"))
        reconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies2", managed_policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess",))
        reconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies3", managed_policy_arn="arn:aws:iam::aws:policy/AmazonAthenaFullAccess"))
        reconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies4", managed_policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"))

        reconciliationTaskExecutionRole = iam.Role(self, "reconciliationTask-executionRole",role_name="reconciliationTask-executionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        reconciliationTaskExecutionRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies5", managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"))

        reconciliationScheduleHandlerRole = iam.Role(
            self,
            "reconciliationScheduleHandlerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(self, "reconciliationScheduleHandlerRole_policy1", managed_policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess"),
                iam.ManagedPolicy.from_managed_policy_arn(self, "reconciliationScheduleHandlerRole_policy2", managed_policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess"),
                iam.ManagedPolicy.from_managed_policy_arn(self, "reconciliationScheduleHandlerRole_policy3", managed_policy_arn="arn:aws:iam::aws:policy/AmazonAthenaFullAccess"),
                iam.ManagedPolicy.from_managed_policy_arn(self, "reconciliationScheduleHandlerRole_policy4", managed_policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"),
                #iam.ManagedPolicy.from_managed_policy_arn(self, "reconciliationScheduleHandlerRole_policy5", managed_policy_arn="arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole")
            ]
        )

        sg = ec2.CfnSecurityGroup(self, "hls-reconciliation",
            vpc_id="vpc-0df5e08d7f490adaa",
            group_name="hls-reconciliation",
            group_description="security group for HLS reconciliation process",
            security_group_ingress=[ec2.CfnSecurityGroup.IngressProperty(
                ip_protocol="tcp",
                cidr_ip="10.15.0.0/16",
                description="inbound rule for private ip block",
                from_port=0,
                to_port=65535
            ),
            ec2.CfnSecurityGroup.IngressProperty(
                ip_protocol="tcp",
                cidr_ip="10.15.0.0/16",
                description="inbound rule for ssh",
                from_port=22,
                to_port=22
            )],
            security_group_egress=[ec2.CfnSecurityGroup.EgressProperty(
                ip_protocol="all",
                cidr_ip="0.0.0.0/0",
                description="allow output to any ipv4 address using any protocol",                                    
                from_port=0,
                to_port=65535
            )]
            )
        
        vpc = ec2.Vpc.from_lookup(self, 'HLS-Production-VPC', vpc_id="vpc-0df5e08d7f490adaa")
        
        cluster = ecs.Cluster(
            self,
            "MyCluster",
            vpc=vpc,
            cluster_name="hls-lpdaac-orchestration-v2",
            #security_groups=[sg],
        )

        reconciliation_task_definition = ecs.FargateTaskDefinition(
            self, "ReconciliationTaskDefinition",
            task_role=reconciliationTaskRole,
            execution_role=reconciliationTaskExecutionRole,
            memory_limit_mib=512,
            cpu=256
        )
        
        asset = ecr_assets.DockerImageAsset(
            self, "ReconciliationTaskImage",
            directory= os.path.join("../script")
        )

        container = reconciliation_task_definition.add_container(
            "ReconciliationTaskContainer",
            image=ecs.ContainerImage.from_docker_image_asset(asset),
            logging=ecs.LogDriver.aws_logs(stream_prefix='my-log-group',log_retention=RetentionDays.FIVE_DAYS)
            #memory_reservation_mib=5120
        )

        # Define the Lambda function
        reconciliation_schedule_handler_func = lambda_.Function(
            self,
            "reconciliationScheduleHandlerFunc",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context):\n    print('Hello, world!')"),
            role=reconciliationScheduleHandlerRole,
            environment={
                'ECS_CLUSTER_NAME': cluster.cluster_name,
                'ECS_TASK_DEFINITION_ARN': reconciliation_task_definition.task_definition_arn
            }
        )

        # Define the CloudWatch scheduled event
        reconciliation_schedule = events.Rule(
            self,
            "reconciliationScheduleHandler",
            schedule=events.Schedule.cron(
                #hour='23',
                minute='*'
            )
        )

        # Add the Lambda function as a target for the CloudWatch event
        reconciliation_schedule.add_target(
            targets.LambdaFunction(
                reconciliation_schedule_handler_func
            )
        )






