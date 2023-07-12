import json

from utils import run_command_and_get_output


class RpmFusionInstalledException(Exception):
    pass


class CantFindDeploymentException(Exception):
    pass


class RpmOstreeDeployment:
    def __init__(
        self,
        image: str = "",
        version: str = "",
        version_nice: str = "",
        base_commit: str = "",
        layered_packages: list[str] = None,
        local_packages: list[str] = None,
        overrides: list[str] = None,
        removals: list[str] = None,
        is_current: bool = False,
        is_pinned: bool = False,
    ):
        self.image = image
        self.version = version
        self.version_nice = version_nice
        self.base_commit = base_commit
        self.layered_packages = layered_packages
        self.local_packages = local_packages
        self.overrides = overrides
        self.is_current = is_current
        self.is_pinned = is_pinned
        self.removals = removals


class RpmOstreeStatus:
    def __init__(self, state: str, deployments: list[RpmOstreeDeployment]):
        self.state = state
        self.deployments = deployments


def rpm_ostree_status() -> RpmOstreeStatus:
    output = run_command_and_get_output("rpm-ostree status --json".split())[0]
    status_json = json.loads(output)

    deployments = []
    for dep in status_json["deployments"]:
        deployment = RpmOstreeDeployment()
        deployment.image = dep["origin"]
        deployment.layered_packages = dep["requested-packages"]
        deployment.local_packages = dep["requested-base-local-replacements"]
        deployment.overrides = dep["requested-local-fileoverride-packages"]
        deployment.removals = dep["requested-base-removals"]
        deployment.version = dep["version"]
        deployment.is_current = dep["booted"]
        deployment.is_pinned = dep["pinned"]
        deployment.base_commit = dep["base-checksum"]

        origin_pieces = dep["origin"].split("/")
        deployment.version_nice = origin_pieces[3] + " " + dep["version"]

        deployments.append(deployment)

    # TODO fix state
    return RpmOstreeStatus("idle", deployments)


def rpm_ostree_install_rpm_fusion() -> bool:
    # TODO see if we can do both steps at once with -A
    rpmfusion_already_installed = False
    rpmfusion_already_versionless = False
    status = rpm_ostree_status()

    deployed_dep = None
    # I wonder if there's a 1-liner for this
    for d in status.deployments:
        if d.is_current:
            deployed_dep = d
            break

    if not deployed_dep:
        raise CantFindDeploymentException()

    rpmfusion_packages = []
    for p in deployed_dep.local_packages:
        if p.startswith("rpmfusion"):
            rpmfusion_already_installed = True
            if p.endswith("free-release"):
                rpmfusion_already_versionless = True
            else:
                rpmfusion_packages.append(p)

    if rpmfusion_already_installed:
        if rpmfusion_already_versionless:
            raise RpmFusionInstalledException()

        cmd = "rpm-ostree update"
        for p in rpmfusion_packages:
            cmd += f" --uninstall {p}"

        cmd += " --install rpmfusion-free-release --install rpmfusion-nonfree-release"
    else:
        cmd = "rpm-ostree install "
        cmd += "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm "
        cmd += "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

    run_command_and_get_output(cmd.split(" "))

    return rpmfusion_already_installed
