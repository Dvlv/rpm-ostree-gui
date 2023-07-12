import json
import subprocess


class RpmOstreeDeployment:
    def __init__(
        self,
        image: str = "",
        version: str = "",
        base_commit: str = "",
        gpg_sig: str = "",
        layered_packages: list[str] = None,
        is_current: bool = False,
    ):
        self.image = image
        self.version = version
        self.base_commit = base_commit
        self.gpg_sig = gpg_sig
        self.layered_packages = layered_packages
        self.is_current = is_current


class RpmOstreeStatus:
    def __init__(self, state: str, deployments: list[RpmOstreeDeployment]):
        self.state = state
        self.deployments = deployments


def run_command_and_get_output(command: list[str]):
    output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output.stdout.decode("utf-8"), output.stderr.decode("utf-8")


def rpm_ostree_status() -> RpmOstreeStatus:
    output = run_command_and_get_output("rpm-ostree status --json".split())[0]
    status_json = json.loads(output)

    print(status_json)

    return RpmOstreeStatus("idle", [])
