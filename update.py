#! /usr/bin/env python3
import hashlib
from datetime import datetime
from pathlib import Path

import requests
from lxml import etree


TARBALL_URL = "https://downloads.plex.tv/plex-desktop/{version}/linux_tarball/Plex-{version}-linux-x86_64.tar.bz2"


def tarball_sha256(url):
  # No .sha256 sidecar is published alongside the tarball, so hash it as it streams.
  digest = hashlib.sha256()
  with requests.get(url, stream=True) as resp:
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
      digest.update(chunk)
  return digest.hexdigest()


def update_yaml(app_id, version):
  tmpl = Path(f"{app_id}.yml.in").read_text()
  url = TARBALL_URL.format(version=version)
  sha = tarball_sha256(url)
  with open(f"{app_id}.yml", "w") as fp:
    tmpl = tmpl.replace("@FULL_VERSION@", version)
    tmpl = tmpl.replace("@TARBALL_SHA256@", sha)
    fp.write(tmpl)


def update_xml(app_id, version):
  xml_filename = f"{app_id}.metainfo.xml"
  parts = version.split(".")
  public_version = f"{parts[0]}.{parts[1]}.{parts[2]}"
  parser = etree.XMLParser(remove_comments=False)
  tree = etree.parse(xml_filename, parser=parser)
  release = etree.Element(
    "release",
    {"version": public_version, "date": datetime.today().strftime("%Y-%m-%d")},  # Thanks spotify <3
  )
  releases = tree.find("releases")
  release.tail = "\n    "
  releases.insert(0, release)
  tree.write(xml_filename, xml_declaration=True, encoding="utf-8")


if __name__ == "__main__":
  from argparse import ArgumentParser

  parser = ArgumentParser()
  parser.add_argument("app_id")
  parser.add_argument("version")
  args = parser.parse_args()

  update_yaml(args.app_id, args.version)
  update_xml(args.app_id, args.version)
