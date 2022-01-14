# Copyright (c) 2019, Hans Jerry Illikainen <hji@dyntopia.com>
#
# SPDX-License-Identifier: BSD-2-Clause

import shutil
import sys
from typing import IO, List, Tuple

import click
import texttable
import json

from . import audit, cache, option, packages


@click.command()
@option.add_config(
    "--config",
    "-c",
    help="Configuration file.",
)
@option.add(
    "--installed",
    "-i",
    is_flag=True,
    help="Audit installed packages.",
)
@option.add(
    "--file",
    "-f",
    "files",
    multiple=True,
    type=click.File(),
    help="Audit packages in file (can be specified multiple times).",
)
@option.add(
    "--username",
    help="Username for authentication.",
)
@option.add(
    "--token",
    help="Token for authentication.",
)
@option.add(
    "--column",
    "columns",
    default=["name", "version", "title"],
    multiple=True,
    show_default=True,
    help="Column to show (can be specified multiple times).",
)
@option.add(
    "--ignore-id",
    "ignore_ids",
    multiple=True,
    help=(
        "Ignore a vulnerability by Sonatype ID or CVE "
        "(can be specified multiple times)."
    ),
)
@option.add(
    "--ignore-cache",
    is_flag=True,
    help="Temporarily ignore existing cache.",
)
@option.add(
    "--reset-cache",
    is_flag=True,
    help="Remove existing cache.",
)
@option.add(
    "--json-output",
    "-j",
    is_flag=True,
    help="Output in JSON string",
)
def cli(
        installed: bool,
        files: List[IO[str]],
        username: str,
        token: str,
        columns: Tuple[str],
        ignore_ids: Tuple[str],
        ignore_cache: bool,
        reset_cache: bool,
        json_output: bool,
) -> None:
    if reset_cache:
        cache.reset()

    pkgs = []  # type: list
    if installed:
        pkgs += packages.get_installed()
    if files:
        pkgs += packages.get_from_files(files)

    try:
        vulns = [
            v for v in audit.components(pkgs, username, token, ignore_cache)
            if v.id not in ignore_ids and v.cve not in ignore_ids
        ]
    except audit.AuditError as e:
        raise click.ClickException(str(e))

    vlen, plen = len(vulns), len(pkgs)
    
    if vulns:
    # Export to JSON
        if json:
            v_dict = []
            for i in range(len(vulns)):
                v_dict.append(vulns[i]._asdict())
            json_string = json.dumps(v_dict)
            print(json_string)
    # ----  
        else:
            size = shutil.get_terminal_size()
            table = texttable.Texttable(max_width=size.columns)
            table.header(columns)
            table.set_cols_dtype(["t" for _ in range(len(columns))])
            table.add_rows([[getattr(v, c.lower(), "")
                         for c in columns]
                        for v in vulns], False)
            click.echo(table.draw())
            click.echo("Found {} vulnerabilities in {} packages".format(vlen, plen))
    else:
        print("[]")
    #Add export to JSON
    
    #out_file = open("myfile.json", "w")
    #v_dict = []
    
    #for i in range(len(vulns)):
    #    v_dict.append(vulns[i]._asdict())

    #json.dump(v_dict, out_file, indent=6)
  
    #out_file.close()
    # ----
    sys.exit(vlen != 0)
