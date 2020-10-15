import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";
const reconciliationTaskRole = new aws.iam.Role("reconciliationTask-taskRole", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
    permissionsBoundary: "arn:aws:iam::611670965994:policy/gcc-tenantOperatorBoundary"
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
    "arn:aws:iam::aws:policy/AWSLambdaFullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerServiceFullAccess"
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
const cluster = new awsx.ecs.Cluster("hls-lpdaac-orchestration", { vpc });
const reconciliationTaskExecutionRole = new aws.iam.Role("reconciliationTask-executionRole", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
    permissionsBoundary: "arn:aws:iam::611670965994:policy/gcc-tenantOperatorBoundary"
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
        memoryReservation: 1280,
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
    permissionsBoundary: "arn:aws:iam::611670965994:policy/gcc-tenantOperatorBoundary"
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach1", {
    role: reconciliationScheduleHandlerRole,
    policyArn: aws.iam.ManagedPolicies.AWSLambdaFullAccess,
});
new aws.iam.RolePolicyAttachment("reconciliationScheduleHandlerRoleAttach2", {
    role: reconciliationScheduleHandlerRole,
    policyArn: aws.iam.ManagedPolicies.AmazonEC2ContainerServiceFullAccess,
});
// More info on Schedule Expressions at
// https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
const reconciliationSchedule = aws.cloudwatch.onSchedule(
    "reconciliationScheduleHandler",
    //"cron(0/1 * * * ? *)",  //run every minute for testing
    "cron(0 6 * * ? *)", //run at 6 AM
    new aws.lambda.CallbackFunction("reconciliationScheduleHandlerFunc", {
        role: reconciliationScheduleHandlerRole,
        callback: async (e) => {
            console.log(`started reconciliationScheduleHandler`);
            await reconciliationTask.run({ cluster });
        }
    })
);
