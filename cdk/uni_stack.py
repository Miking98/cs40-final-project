import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as r53

from config import settings
from aws_cdk import aws_logs as logs

class UniStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ########################################################
        ########################################################
        #
        # Networking
        #
        ########################################################
        ########################################################

        self.vpc = ec2.Vpc(
            self,
            f"{settings.PROJECT_NAME}-vpc",
            availability_zones=['us-west-2a','us-west-2b'],
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[ 
                { 'cidrMask': 24, 'name': 'ingress', 'subnetType': ec2.SubnetType.PUBLIC, }, 
                { 'cidrMask': 24, 'name': 'application', 'subnetType': ec2.SubnetType.PRIVATE_WITH_EGRESS, }, 
                { 'cidrMask': 24, 'name': 'rds', 'subnetType': ec2.SubnetType.PRIVATE_ISOLATED, }
            ],
        )
        self.backend_certificate = acm.Certificate(
            self,
            f"{settings.PROJECT_NAME}-backend-certificate",
            domain_name="mwornow.infracourse.cloud",
            subject_alternative_names=["*.mwornow.infracourse.cloud", ],
            validation=acm.CertificateValidation.from_dns(
                hosted_zone=props.hosted_zone
            ),
        )


        ########################################################
        ########################################################
        #
        # Database
        #
        ########################################################
        ########################################################

        self.aurora_db = rds.ServerlessCluster(
            self,
            f"{settings.PROJECT_NAME}-aurora-serverless",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_2_10_2,
            ),
            default_database_name=settings.DB_NAME,
            credentials=rds.Credentials.from_generated_secret(
                username="admin",
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
        )

        ########################################################
        ########################################################
        #
        # Compute
        #
        ########################################################
        ########################################################
        
        cluster = ecs.Cluster(
            self, 
            f"{settings.PROJECT_NAME}-cluster", 
            vpc=self.vpc,
        )

        fargate_task_definition = ecs.FargateTaskDefinition(
            self,
            f"{settings.PROJECT_NAME}-fargate-task-definition",
            cpu=512,
            memory_limit_mib=2048,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64
            ),
        )

        self.aurora_db.secret.grant_read(fargate_task_definition.task_role)

        # FILLMEIN: Add a container to the Fargate task definition
        fargate_task_definition.add_container(
            f"{settings.PROJECT_NAME}-app-container",
            image=ecs.ContainerImage.from_registry('wordpress'),
            logging=ecs.AwsLogDriver(
                stream_prefix=f"{settings.PROJECT_NAME}-fargate",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            port_mappings=[ecs.PortMapping(container_port=80, host_port=80)],
            environment={
                "WORDPRESS_DB_HOST": self.aurora_db.cluster_endpoint.hostname,
                "WORDPRESS_DB_USER": "admin",
                "WORDPRESS_DB_NAME": "db_wordpress",
            },
            secrets={
                "WORDPRESS_DB_PASSWORD": ecs.Secret.from_secrets_manager(self.aurora_db.secret, field="password"),
            },
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"{settings.PROJECT_NAME}-fargate-service",
            domain_name='mwornow.infracourse.cloud',
            domain_zone=props.hosted_zone,
            certificate=self.backend_certificate,
            redirect_http=True,
            task_definition=fargate_task_definition,
            cluster=cluster,
        )

        fargate_service.target_group.configure_health_check(path="/wp-admin/setup-config.php")

        fargate_service.service.connections.allow_to(
            self.aurora_db, ec2.Port.tcp(3306), "DB access"
        )
