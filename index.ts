import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";


const reconciliationTaskRole = new aws.iam.Role("reconciliationTask-taskRole", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
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
}

const cluster = new awsx.ecs.Cluster("hls-lpdaac-orchestration");

const reconciliationTask = new awsx.ecs.FargateTaskDefinition("reconciliationTask", {
    taskRole: reconciliationTaskRole,
    container: {
        image: awsx.ecs.Image.fromPath("reconciliationTask", "./script"),
        memoryReservation: 128,
    },
});

const reconciliationScheduleHandler = async (event) => {
    console.log(`started reconciliationScheduleHandler`);
    await reconciliationTask.run({ cluster });
};

// More info on Schedule Expressions at
// https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
const reconciliationSchedule = aws.cloudwatch.onSchedule(
    "reconciliationScheduleHandler",
    //"cron(0/1 * * * ? *)",  //run every minute for testing
    "cron(0 6 * * ? *)", //run at 6 AM
    reconciliationScheduleHandler,
);
