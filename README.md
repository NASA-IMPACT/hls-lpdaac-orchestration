# HLS LPDAAC ORCHESTRATION

This resposity contains HLS LPDAAC Orchestration Python Script, Docker container and Pulumi Deployment Script to run the docker container as Fargate task on a schedule

## Automated Deployment Prerequisite
* Install Node Version Manager (nvm)
* Install Node.js using nvm
* Install Docker and setup up appropriate permission to run Docker without sudo
* Install https://www.pulumi.com/

## Automated Deployment
* Clone the repository and make sure you are on the correct branch
* Login to pulumi `pulumi login --local`
* Deploy the stack with command `pulumi up`
    * Choose the stack name `hls-lpdaac-orchestration` if asked
    * Note: main deployment code is in `index.ts` file

