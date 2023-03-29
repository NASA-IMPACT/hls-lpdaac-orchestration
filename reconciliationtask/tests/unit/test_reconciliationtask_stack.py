import aws_cdk as core
import aws_cdk.assertions as assertions

from reconciliationtask.reconciliationtask_stack import ReconciliationtaskStack

# example tests. To run these tests, uncomment this file along with the example
# resource in reconciliationtask/reconciliationtask_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ReconciliationtaskStack(app, "reconciliationtask")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
