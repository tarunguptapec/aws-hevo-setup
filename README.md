## Prerequisites ##
1) Make sure that aws-cli is installed.
2) Setup a wildcard certificate for \*.company.com in AWS Certificate Manager and get the certificate arn.

## setup.py ##

This file uses aws-cli and boto-3 library to instantiate infrastructure required for hevo on premise installation. It creates the following resources in the AWS infrastructure.
- Key-Pair: - 'hevo-company-name'
- VPC: 'hevo-company-name-vpc'
- Internet Gateway: 'hevo-company-name-ig'
- Subnet: 'hevo-company-name'
- Security Group: 'hevo-company-name-sg'
- IAM Role: 'hevo-company-name-role'
- IAM Policy: 'hevo-company-name-policy'
- VPC Peering Connection: company-name + '-hevo'
- Hevo EC2 Instances
- ELB: 'hevo-company-name-elb'