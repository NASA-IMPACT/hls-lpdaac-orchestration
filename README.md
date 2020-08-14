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
* Deploy the stack with command `pulumi up`
    * Hit enter to create a new stack
    * Enter passphrase for the stack
    * Note: main deployment code is in `index.ts` file

