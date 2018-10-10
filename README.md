## Prerequisites ##
1) Make sure that aws-cli is installed.
2) Setup a wildcard certificate for \*.company.com in AWS Certificate Manager and get the certificate arn.

## setup.py ##

This file uses aws-cli and boto-3 library to instantiate infrastructure required for hevo on premise installation. It creates the following resources in the AWS infrastructure.
- Key-Pair: - 'hevo-company'
- VPC: 'hevo-company-vpc'
- Internet Gateway: 'hevo-company-ig'
- Subnet: 'hevo-company'
- Security Group: 'hevo-company-sg'
- IAM Role: 'hevo-company-role'
- IAM Policy: 'hevo-company-policy'
- VPC Peering Connection: 'company-hevo-vpc'
- Hevo EC2 Instances
- ELB: 'hevo-company-elb'