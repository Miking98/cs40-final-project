import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as r53

from config import settings
from aws_cdk import aws_logs as logs

class DnsStack(cdk.Stack):
    hosted_zone: r53.IHostedZone

    def __init__(self, scope: cdk.App, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ########################################################
        ########################################################
        #
        # Networking
        #
        ########################################################
        ########################################################

        self.hosted_zone = r53.HostedZone(
            self,
            f"{settings.PROJECT_NAME}-hosted-zone",
            zone_name='mwornow.infracourse.cloud',
        )