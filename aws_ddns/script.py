#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""aws_ddns.py

A script that updates an A record in AWS Route 53 with the current
public IP address of the machine running the script.

This is useful for maintaining a dynamic DNS entry for a home server
or any device with a changing IP address.
"""

import logging
import re
import sys
import tomllib

from pathlib import Path
from urllib import request

import boto3
import typer

from rich.pretty import pretty_repr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Make the script a typer appplication
app = typer.Typer()


def load_toml_config(fpath: Path) -> dict:
    """Load a TOML configuration for pyani-benchmark"""
    with fpath.open("rb") as ifh:
        return tomllib.load(ifh)["aws_ddns"]


def get_current_ip(ipservice: str) -> str:
    """Returns current IP address"""
    ipaddr = request.urlopen(ipservice).read().decode("utf8").strip()
    if not re.match("^[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$", ipaddr):
        msg = f"{ipservice} returns invalid IP: {ipaddr}"
        raise ValueError(msg)
    return ipaddr


def make_json_update(ipaddr: str, config: dict) -> dict:
    """Returns JSON for Route 53 IP address update"""
    data = {
        "Comment": "Updated From DDNS Shell Script",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "ResourceRecords": [{"Value": ipaddr}],
                    "Name": config["name"],
                    "Type": config["type"],
                    "TTL": config["ttl"],
                },
            }
        ],
    }
    return data


@app.command()
def main(configpath: Path=Path.home() / ".aws_ddns.toml",
         ipservice: str = typer.Option("https://checkip.amazonaws.com", "--ip-service"), 
         log_level: str = typer.Option("INFO", "--log-level")) -> None:
    """Update a Route 53 record with the current external IP address"""
    # Set log level based on user input
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Load TOML config
    config = load_toml_config(configpath)
    logger.debug(f"Processing config file: {configpath}\n{pretty_repr(config)}")

    # Get local public IP address
    try:
        ipaddr = get_current_ip(ipservice)
    except ValueError as err:
        logger.error(err)
        sys.exit(1)
    logger.info(f"Current public IP address: {ipaddr}")

    # Connect to Route53
    client = boto3.client("route53")
    recordsets = client.list_resource_record_sets(
        HostedZoneId=config["hosted_zone_id"],
        StartRecordName=config["name"],
        StartRecordType=config["type"],
    )
    current_r53_ipaddr = recordsets["ResourceRecordSets"][0]["ResourceRecords"][0][
        "Value"
    ]
    logger.info(f"Current Route 53 IP address: {current_r53_ipaddr}")

    if ipaddr == current_r53_ipaddr:
        logger.info("IP has not changed, exiting")
        sys.exit(0)
    else:
        changebatch = make_json_update(ipaddr, config)
        logger.debug(f"Making Route 53 batch call:\n{pretty_repr(changebatch)}")
        retval = client.change_resource_record_sets(
            HostedZoneId=config["hosted_zone_id"], ChangeBatch=changebatch
        )
        logger.debug(f"Route 53 call returns: \n {pretty_repr(retval)}")


if __name__ == "__main__":
    app()
