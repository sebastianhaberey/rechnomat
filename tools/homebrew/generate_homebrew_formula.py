#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import socket
import textwrap
from dataclasses import dataclass
from pathlib import Path

import requests
import urllib3
from packaging.markers import Environment, default_environment
from packaging.requirements import Requirement
from packaging.utils import parse_wheel_filename
from packaging.version import Version


def allowed_gai_family():
    return socket.AF_INET  # Force IPv4


# Force urllib3 to use IPv4
urllib3.util.connection.allowed_gai_family = allowed_gai_family


@dataclass(frozen=True)
class Bottle:
    macos_path: Path
    linux_path: Path
    root_url: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_bottle_platform(path: Path) -> str:
    name = path.name  # e.g. "easyborg--0.15.2.arm64_sequoia.bottle.1.tar.gz"

    before_bottle, _, _ = name.partition(".bottle")
    platform = before_bottle.split(".")[-1]

    if not platform:
        raise RuntimeError(f"Could not infer Homebrew platform from bottle filename: {name}")

    print(f"Inferred Homebrew platform {platform} from bottle filename: {path}")

    return platform


def major_minor(pyver: str) -> str:
    return ".".join(pyver.split(".")[:2])


def fetch_pypi_metadata(package: str, version: str | None = None) -> dict:
    """Fetch PyPI JSON for package, optionally pinned to version."""
    if version:
        url = f"https://pypi.org/pypi/{package}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{package}/json"

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Could not fetch PyPI metadata for {package} (version={version})")

    return resp.json()


def find_url(meta: dict, packagetype: str) -> dict | None:
    """Find a download url of the given packagetype in metadata, or None if there isn't one."""
    for url in meta["urls"]:
        if url["packagetype"] == packagetype:
            return url

    return None


def get_url(meta: dict, packagetype: str) -> dict:
    """Choose a download url of the given packagetype from metadata, raising if there isn't one."""
    url = find_url(meta, packagetype)
    if url is None:
        raise RuntimeError(f"No usable {packagetype} distribution for {meta['info']['name']}.")

    return url


def is_macos_arm64_tag(platform_tag: str) -> bool:
    return platform_tag.startswith("macosx") and ("arm64" in platform_tag or "universal2" in platform_tag)


def is_linux_x86_64_tag(platform_tag: str) -> bool:
    return "linux" in platform_tag and platform_tag.endswith("x86_64")


def matches_interpreter(tag, python_version: str) -> bool:
    """
    True if a wheel tag is usable with target_python_version: either interpreter-agnostic
    ("py3"/"none"/"abi3", e.g. playwright) or built for that exact CPython version's regular
    (non-free-threaded) ABI, e.g. "cp314-cp314-..." but not "cp314-cp314t-...".
    """
    cpython_tag = "cp" + major_minor(python_version).replace(".", "")
    return tag.interpreter in ("py3", cpython_tag) and tag.abi in ("none", "abi3", cpython_tag)


def get_wheel_urls_for_platforms(meta: dict, python_version: str) -> dict[str, dict]:
    """
    Resolve one wheel per Homebrew bottle platform we build for (macOS arm64, Linux x86_64) and
    matching python_version, for packages that can't go through brew's normal
    virtualenv_install_with_resources build-from-source path (no sdist, or an sdist that can't
    be built in Homebrew's sandbox).
    """
    predicates = {
        "macos_arm64": is_macos_arm64_tag,
        "linux_x86_64": is_linux_x86_64_tag,
    }
    resolved: dict[str, dict] = {}

    for url in meta["urls"]:
        if url["packagetype"] != "bdist_wheel":
            continue

        _, _, _, tags = parse_wheel_filename(url["filename"])
        matching_tags = [tag for tag in tags if matches_interpreter(tag, python_version)]

        for platform_key, predicate in predicates.items():
            if platform_key not in resolved and any(predicate(tag.platform) for tag in matching_tags):
                resolved[platform_key] = {"url": url["url"], "sha256": url["digests"]["sha256"]}

    missing = predicates.keys() - resolved.keys()
    if missing:
        raise RuntimeError(
            f"No wheel found for {meta['info']['name']} matching platform(s): {', '.join(sorted(missing))}."
        )

    return resolved


def build_marker_env(target_python_version: str) -> Environment:
    """Environment for PEP 508 marker evaluation."""
    env = default_environment()
    env["python_version"] = major_minor(target_python_version)
    env["python_full_version"] = target_python_version
    env["extra"] = None
    return env


def get_matching_version(metadata: dict, requirement: Requirement) -> str | None:
    if not requirement.specifier:  # no pinned version, return current version
        return metadata["info"]["version"]

    versions = sorted((Version(v) for v in metadata["releases"] if v), reverse=True)
    for version in versions:
        if version in requirement.specifier:
            return str(version)

    raise RuntimeError(f"Could not find version satisfying {requirement} for {requirement.name}")


# Packages that publish an sdist, but whose build can't run in Homebrew's sandboxed build phase
# (e.g. pydantic_core needs the Rust-based maturin build backend, which itself needs network
# access to fetch crates - unavailable mid-build). These always resolve to per-platform wheels
# instead, even though an sdist technically exists.
FORCE_WHEEL_PACKAGES = {"pydantic_core"}


def resolve_dependencies_from_pypi(root_package: str, root_version: str, python_version: str) -> dict[str, dict]:
    """
    Returns mapping: package -> { "kind": "sdist", "version": ..., "url": ..., "sha256": ... }
    or (for wheel-only packages) package -> { "kind": "wheel", "version": ..., "platforms": {...} }
    """

    env = build_marker_env(python_version)
    todo = [(root_package, root_version)]
    resolved: dict[str, dict] = {}

    while todo:
        package, version = todo.pop()

        if package in resolved:
            continue

        metadata = fetch_pypi_metadata(package, version)
        info = metadata["info"]
        name = info["name"]

        if name == root_package:
            url = get_url(metadata, "sdist")  # use sdist for root package (required for brew)
            resolved[name] = {
                "kind": "sdist",
                "version": version,
                "url": url["url"],
                "sha256": url["digests"]["sha256"],
            }
        else:
            # brew's virtualenv_install_with_resources extracts each resource archive and runs
            # `pip install <extracted_dir>`, which requires a source distribution. Prefer sdist;
            # if a dependency doesn't publish one (e.g. playwright) or can't be built from one in
            # Homebrew's sandbox (FORCE_WHEEL_PACKAGES), fall back to per-platform wheels
            # installed directly (see generate_formula/{{WHEEL_RESOURCES}}).
            sdist_url = None if name in FORCE_WHEEL_PACKAGES else find_url(metadata, "sdist")
            if sdist_url:
                resolved[name] = {
                    "kind": "sdist",
                    "version": version,
                    "url": sdist_url["url"],
                    "sha256": sdist_url["digests"]["sha256"],
                }
            else:
                resolved[name] = {
                    "kind": "wheel",
                    "version": version,
                    "platforms": get_wheel_urls_for_platforms(metadata, python_version),
                }

        requires_dist = info.get("requires_dist") or []
        for requirement_str in requires_dist:
            requirement = Requirement(requirement_str)

            if requirement.marker and not requirement.marker.evaluate(env):
                continue

            metadata = fetch_pypi_metadata(requirement.name)
            version = get_matching_version(metadata, requirement)
            todo.append((requirement.name, version))

    return resolved


def generate_formula(
    package: str,
    template: str,
    metadata: dict,
    python_version: str,
    *,
    bottle: Bottle = None,
) -> str:
    """Generate final formula text."""
    resource_blocks = []
    wheel_resource_blocks = []
    wheel_names = []

    for name, info in sorted(metadata.items()):
        if name.lower() == package.lower():
            continue

        if info["kind"] == "sdist":
            block = f"""
resource "{name}" do
  url "{info["url"]}"
  sha256 "{info["sha256"]}"
end
            """
            resource_blocks.append(textwrap.indent(block.strip(), "  "))
        else:
            macos = info["platforms"]["macos_arm64"]
            linux = info["platforms"]["linux_x86_64"]
            block = f"""
resource "{name}" do
  on_macos do
    on_arm do
      url "{macos["url"]}"
      sha256 "{macos["sha256"]}"
    end
  end
  on_linux do
    url "{linux["url"]}"
    sha256 "{linux["sha256"]}"
  end
end
            """
            wheel_resource_blocks.append(textwrap.indent(block.strip(), "  "))
            wheel_names.append(name)

    resources_text = "\n\n".join(resource_blocks)
    wheel_resources_text = "\n\n".join(wheel_resource_blocks)
    without_resources = "[" + ", ".join(f'"{name}"' for name in wheel_names) + "]"
    wheel_install_steps = "\n".join(
        f'    resource("{name}").fetch\n'
        f'    system libexec/"bin/pip", "install", "--no-deps", resource("{name}").cached_download'
        for name in wheel_names
    )

    root = metadata[package]

    if bottle:
        bottles: dict[str, str] = {}

        platform = infer_bottle_platform(bottle.macos_path)
        bottles[platform] = sha256_file(bottle.macos_path)

        platform = infer_bottle_platform(bottle.linux_path)
        bottles[platform] = sha256_file(bottle.linux_path)

        lines = ["  bottle do", f'    root_url "{bottle.root_url}"']
        for platform, sha in bottles.items():
            lines.append(f'    sha256 cellar: :any_skip_relocation, {platform}: "{sha}"')
        lines.append("  end")
        bottles_block = "\n".join(lines)
    else:
        bottles_block = ""

    return (
        template.replace("{{URL}}", root["url"])
        .replace("{{SHA256}}", root["sha256"])
        .replace("{{RESOURCES}}", resources_text)
        .replace("{{WHEEL_RESOURCES}}", wheel_resources_text)
        .replace("{{WITHOUT_RESOURCES}}", without_resources)
        .replace("{{WHEEL_INSTALL_STEPS}}", wheel_install_steps)
        .replace("{{PYTHON_VERSION}}", major_minor(python_version))
        .replace("{{BOTTLES_BLOCK}}", bottles_block)
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--package", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--python-version", required=True)
    p.add_argument("--template", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--bottle-macos-path", required=False)
    p.add_argument("--bottle-linux-path", required=False)
    p.add_argument("--bottle-root-url", required=False)
    args = p.parse_args()

    print(f"Resolving dependencies for {args.package}=={args.version}…")
    all_meta = resolve_dependencies_from_pypi(
        args.package,
        args.version,
        args.python_version,
    )

    print("Fetching distribution metadata from PyPI…")
    template = Path(args.template).read_text()

    if args.bottle_macos_path and args.bottle_linux_path and args.bottle_root_url:
        bottle = Bottle(
            macos_path=Path(args.bottle_macos_path),
            linux_path=Path(args.bottle_linux_path),
            root_url=args.bottle_root_url,
        )
        print(f"Received bottle arguments: {bottle}")
    elif args.bottle_macos_path or args.bottle_linux_path or args.bottle_root_url:
        raise ValueError("All bottle-related arguments must be passed, or none.")
    else:
        bottle = None

    formula = generate_formula(
        args.package,
        template,
        all_meta,
        args.python_version,
        bottle=bottle,
    )

    Path(args.output).write_text(formula)
    print(f"Formula written to {args.output}")


if __name__ == "__main__":
    main()
