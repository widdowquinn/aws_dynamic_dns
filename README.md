# README.md `aws_dynamic_dns`

This `README.md` file describes how to use the `aws_ddns.py` script in the `aws_dynamic_ddns` repository to use AWS Route 53 as a dynamic DNS service.

```bash
% aws_ddns --help

 Usage: aws_ddns [OPTIONS]

 Update a Route 53 record with the current external IP address

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --configpath                PATH  [default: ~/.aws_ddns.toml]                │
│ --ip-service                TEXT  [default: https://checkip.amazonaws.com]   │
│ --log-level                 TEXT  [default: INFO]                            │
│ --install-completion              Install completion for the current shell.  │
│ --show-completion                 Show completion for the current shell, to  │
│                                   copy it or customize the installation.     │
│ --help                            Show this message and exit.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Prerequisites

To use this script effectively you will need:

- An AWS account
- An AWS IAM account with Route 53 permissions
- Local credentials installed for the AWS IAM account
- A domain name registered with Route 53
- A Route 53 Hosted Zone for your domain name
- A type A record for your Route 53 Hosted Zone

## Installation

Clone this repository and install with

```bash
pip install -e .
```

This will install the `aws_ddns` script, which you should be able to check using:

```bash
aws_ddns --help
```

## Configuration

`aws_ddns` uses your local AWS credentials _via_ `boto3`, and will not ask for authentication information.

`aws_ddns` reads information from a TOML format configuration file (default location: `~/.aws_ddns.toml`), e.g.

```toml
[aws_ddns]
hosted_zone_id="Zxxxxxxxxxxxxx"
name="[DOMAIN_NAME]."
type="A"
ttl=300
```

where the `hosted_zone_id` can be obtained from the Route 53 interface, and `[DOMAIN_NAME]` is the domain you wish to point to the IP address. Note that there is a period/full stop (`.`) after the domain name.

## How it works

- configuration information is loaded (by default from `~/.aws_ddns.toml` but this can be changed with the `--configpath` option)
- the current public-facing external IP of the machine is checked (by default, at `https://checkip.amazonaws.com`, but this can be changed with the `--ip-service` option). 
- local `boto3` authentication is used to connect to Route 53 using the configuration options to identify the IP address currently associated with the domain name. If this matches the current external IP address, the script exits. Otherwise, the script will update the Route 53 record.
