# HLS LPDAAC ORCHESTRATION

This resposity contains HLS LPDAAC Orchestration Python Script, Docker container and Pulumi Deployment Script to run the docker container as Fargate task on a schedule

## Automated Deployment Prerequisite
* Install Node Version Manager (nvm) - https://nodesource.com/blog/installing-node-js-tutorial-using-nvm-on-mac-os-x-and-ubuntu/
* Install Node.js using nvm
* Install npm - https://www.e2enetworks.com/help/how-to-install-nodejs-npm-on-ubuntu/
* Install Docker and setup up appropriate permission to run Docker without sudo - https://medium.com/@cjus/installing-docker-ce-on-an-aws-ec2-instance-running-ubuntu-16-04-f42fe7e80869
* Install https://www.pulumi.com/docs/get-started/install/

## Automated Deployment
* Clone the repository and make sure you are on the correct branch
* run `npm install`
* Login to pulumi `pulumi login --local`
* Select your desired aws region `pulumi config set aws:region <value>`
* Deploy the stack with command `pulumi up`
    * Hit enter to create a new stack
    * Enter passphrase for the stack
    * Note: main deployment code is in `index.ts` file
    
## Deploying in Goddard Commercial Cloud (GCC)
* GCC does not have a default VPC, thus we have to specify a VPC from an existing id in the index.ts file (example below) <br/>

`const vpc = awsx.ec2.Vpc.fromExistingIds("my-vpc", {
    vpcId: "vpc-40b38f25",
    // publicSubnetIds: [],
    // privateSubnetIds: [],
});
const cluster = new awsx.ecs.Cluster("hls-lpdaac-orchestration",{vpc});`

* GCC also restricts users from creating roles without permissions boundaries set so we also need to update the new role command in the index.ts file (example below) <br/>

`const reconciliationTaskRole = new aws.iam.Role("reconciliationTask-taskRole", {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
        }),
    permissionsBoundary: "arn:aws:iam::123456789012:policy/gcc-tenantOperatorBoundary"
});`
