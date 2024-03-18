from aws_cdk import aws_route53 as r53

class Settings:
    PROJECT_NAME: str = 'cs40'
    DB_NAME: str = "db_wordpress"

class Props:
    hosted_zone: r53.IHostedZone
    
settings = Settings()