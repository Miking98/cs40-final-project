import aws_cdk as cdk
from uni_stack import UniStack
from config import Props, settings
from dns_stack import DnsStack

app = cdk.App()
props = Props()

env = cdk.Environment(account='810016509436', region='us-west-2')
dns_stack = DnsStack(app, 
                     f"{settings.PROJECT_NAME}-dns-stack", 
                     env=env)
props.hosted_zone = dns_stack.hosted_zone

UniStack(app, 
         f"{settings.PROJECT_NAME}-uni-stack", 
         props,
         env=env)
app.synth()
