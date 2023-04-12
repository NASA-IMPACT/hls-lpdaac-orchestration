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

        lpdaacOrchestrationReconciliationTaskRole = iam.Role(self, "lpdaac-orchestration-reconciliation-task-role",role_name="lpdaac-orchestration-reconciliationTask",
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
            roles=[lpdaacOrchestrationReconciliationTaskRole.role_name])

        lpdaacOrchestrationReconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-role-add-managed-policies1",managed_policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess"))
        lpdaacOrchestrationReconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-role-add-managed-policies2", managed_policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess",))
        lpdaacOrchestrationReconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-role-add-managed-policies3", managed_policy_arn="arn:aws:iam::aws:policy/AmazonAthenaFullAccess"))
        lpdaacOrchestrationReconciliationTaskRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-role-add-managed-policies4", managed_policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"))

        lpdaacOrchestrationReconciliationTaskExecutionRole = iam.Role(self, "lpdaac-orchestration-reconciliation-task-execution-role",role_name="lpdaac-orchestration-reconciliation-task-execution-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        lpdaacOrchestrationReconciliationTaskExecutionRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "add_managed_policies5", managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"))

        lpdaacOrchestrationReconciliationScheduleHandlerRole = iam.Role(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        lpdaacOrchestrationReconciliationScheduleHandlerRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role_policy1", managed_policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess"))
        lpdaacOrchestrationReconciliationScheduleHandlerRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role_policy2", managed_policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess"))
        lpdaacOrchestrationReconciliationScheduleHandlerRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role_policy3", managed_policy_arn="arn:aws:iam::aws:policy/AmazonAthenaFullAccess"))
        lpdaacOrchestrationReconciliationScheduleHandlerRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role_policy4", managed_policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"))
        lpdaacOrchestrationReconciliationScheduleHandlerRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(self, "lpdaac-orchestration-reconciliation-task-scheduler-handler-role_policy5", managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"))

        sg = ec2.CfnSecurityGroup(self, "lpdaac-orchestration-reconciliation-task-security-group",
            vpc_id="vpc-0df5e08d7f490adaa",
            group_name="lpdaac-orchestration-reconciliation-task-security-group",
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
            cluster_name="hls-lpdaac-orchestration-reconciliation",
            #security_groups=[sg],
        )

        lpdaac_orchestration_reconciliation_task_definition = ecs.FargateTaskDefinition(
            self, "ReconciliationTaskDefinition",
            task_role=lpdaacOrchestrationReconciliationTaskRole,
            execution_role=lpdaacOrchestrationReconciliationTaskExecutionRole,
            runtime_platform=ecs.RuntimePlatform(
            operating_system_family=ecs.OperatingSystemFamily.LINUX,
            cpu_architecture=ecs.CpuArchitecture.ARM64,
            ),
            memory_limit_mib=512,
            cpu=256
        )
        
        asset = ecr_assets.DockerImageAsset(
            self, "ReconciliationTaskImage",
            directory= os.path.join("../script")            
        )

        lpdaac_orchestration_reconciliation_task_definition.add_container(
            "ReconciliationTaskContainer",
            image=ecs.ContainerImage.from_docker_image_asset(asset),
            logging=ecs.LogDriver.aws_logs(stream_prefix='my-log-group',log_retention=RetentionDays.FIVE_DAYS)
            #memory_reservation_mib=5120
        )

        # Define the Lambda function
        lpdaac_orchestration_reconciliation_schedule_handler_func = lambda_.Function(
            self,
            "reconciliationScheduleHandlerFunc",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context):\n    print('Hello, world!')"),
            role=lpdaacOrchestrationReconciliationScheduleHandlerRole
        )

        # Define the CloudWatch scheduled event
        lpdaac_orchestration_reconciliation_schedule = events.Rule(
            self,
            "lpdaacOrchestrationReconciliationSchedule",
            schedule=events.Schedule.cron(
                #hour='23',
                minute='*'
            )
        )

        # Add the Lambda function as a target for the CloudWatch event
        lpdaac_orchestration_reconciliation_schedule.add_target(
            targets.LambdaFunction(
                lpdaac_orchestration_reconciliation_schedule_handler_func
            )
        )






