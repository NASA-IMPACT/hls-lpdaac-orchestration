import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";
const reconciliationTaskRole = new aws.iam.Role("reconciliationTask-taskRole-v2", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
    permissionsBoundary: "arn:aws:iam::611670965994:policy/mcp-tenantOperator"
});
const gccAssumeRolePolicy = new aws.iam.Policy("assumeGCCRolePolicy", {
    policy: {
        Version: "2012-10-17",
        Statement: [{
            Sid: "AssumeRole",
            Effect: "Allow",
            Resource: "*",
            Action: "sts:AssumeRole",
        }],
    },
});
let counter = 0;
const rpa = new aws.iam.RolePolicyAttachment(`reconciliationTask-policy-${counter++}`,
    { policyArn: gccAssumeRolePolicy.arn, role: reconciliationTaskRole },
);
const managedPolicyArns: string[] = [
    "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess",
    "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess"
];
for (const policy of managedPolicyArns) {
    const rpa = new aws.iam.RolePolicyAttachment(`reconciliationTask-policy-${counter++}`,
        { policyArn: policy, role: reconciliationTaskRole },
    );
};
const vpc = awsx.ec2.Vpc.fromExistingIds("HLS-Production-VPC", {
    vpcId: "vpc-090abb90ed08fb5ac",
    publicSubnetIds: ["subnet-0ddcc2e2e0d6c22d1"],
    // privateSubnetIds: [],
    });
const sg = new awsx.ec2.SecurityGroup("hls-reconciliation", { 
    vpc,
    tags: {
        "Name": "hls-reconciliation-SG"
    }, 
    description: "security group for HLS reconciliation process" }
);
const sgrule1 = new aws.ec2.SecurityGroupRule("private-ip-block", {
    type: "ingress",
    fromPort: 0,
    toPort: 65535,
    protocol: "tcp",
    cidrBlocks: ["10.15.0.0/16"],
    securityGroupId: sg.id,
    description: "inbound rule for private ip block",
    });
const sgrule2 = new aws.ec2.SecurityGroupRule("ssh-ip-block", {
    type: "ingress",
    fromPort: 22,
    toPort: 22,
    protocol: "tcp",
    cidrBlocks: ["10.15.0.0/16"],
    securityGroupId: sg.id,
    description: "inbound rule for ssh",
    });
const sgrule3 = new aws.ec2.SecurityGroupRule("outbound-rule", {
    type: "egress",
    fromPort: 0,
    toPort: 65535,
    protocol: "all",
    cidrBlocks: ["0.0.0.0/0"],
    securityGroupId: sg.id,
    description: "allow output to any ipv4 address using any protocol",
    });
const cluster = new awsx.ecs.Cluster("hls-lpdaac-orchestration-historical-v2", { 
   vpc,
   securityGroups: [sg.id]}
   );
const reconciliationTaskExecutionRole = new aws.iam.Role("reconciliationTask-executionRole", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
    permissionsBoundary: "arn:aws:iam::611670965994:policy/mcp-tenantOperator"
});
new aws.iam.RolePolicyAttachment("reconciliationTaskExecutionRoleAttach", {
    role: reconciliationTaskExecutionRole,
    policyArn: 'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',     
});
const reconciliationTask = new awsx.ecs.FargateTaskDefinition("reconciliationTask", {
    taskRole: reconciliationTaskRole,
    executionRole: reconciliationTaskExecutionRole,
    container: {
        image: awsx.ecs.Image.fromPath("reconciliationTask", "./script"),
        memoryReservation: 5120,
    },
});
const reconciliationScheduleHandlerRole = new aws.iam.Role("reconciliationScheduleHandlerRole", {
    assumeRolePolicy: {
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Principal: {
                Service: "lambda.amazonaws.com",
            },
            Effect: "Allow",
            Sid: "",
        }],
    },
    permissionsBoundary: "arn:aws:iam::611670965994:policy/mcp-tenantOperator"
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach1", {
    role: reconciliationScheduleHandlerRole,
    policyArn: 'arn:aws:iam::aws:policy/AWSLambda_FullAccess',
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach2", {
    role: reconciliationScheduleHandlerRole,
    policyArn: 'arn:aws:iam::aws:policy/AmazonECS_FullAccess',
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach3", {
    role: reconciliationScheduleHandlerRole,
    policyArn: 'arn:aws:iam::aws:policy/AmazonAthenaFullAccess',
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach4", {
    role: reconciliationScheduleHandlerRole,
    policyArn: 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach5", {
    role: reconciliationScheduleHandlerRole,
    policyArn: 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
});
// More info on Schedule Expressions at
// https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
const reconciliationSchedule = aws.cloudwatch.onSchedule(
    "reconciliationScheduleHandler",
    //"cron(0/1 * * * ? *)",  //run every minute for testing
    "cron(0 23 * * ? *)", //run at 11 PM
    new aws.lambda.CallbackFunction("reconciliationScheduleHandlerFunc", {
        role: reconciliationScheduleHandlerRole,
        callback: async (e) => {
            console.log(`started reconciliationScheduleHandler`);
            await reconciliationTask.run({ cluster });
        }
    })
);
