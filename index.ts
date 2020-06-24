import * as awsx from "@pulumi/awsx";
import * as aws from "@pulumi/aws";


const cluster = new awsx.ecs.Cluster("hls-lpdaac-orchestration");
const img = awsx.ecs.Image.fromPath("hls-lpdaac-orchestration-img", "./script");

//example ref - https://www.pulumi.com/docs/tutorials/aws/video-thumbnailer/
const reconciliationTask = new awsx.ecs.FargateTaskDefinition("reconciliationTask", {
    container: {
        image: awsx.ecs.Image.fromPath("reconciliationTask", "./script"),
        memoryReservation: 128,
    },
});

const reconciliationScheduleHandler = async (event) => {
    reconciliationTask.run({ cluster });
};


// More info on Schedule Expressions at
// https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
const reconciliationSchedule = aws.cloudwatch.onSchedule(
    "reconciliationScheduleHandler",
    "cron(0 12 * * ? *)",
    reconciliationScheduleHandler,
);
