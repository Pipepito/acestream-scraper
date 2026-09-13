"""Run with the bundled ZeroNet interpreter in a network-disabled container.

Uses real upstream code and cryptography; only site state/task ownership is fake.
--apply-patch allows checking the installer patch against an existing pinned image.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


def main():
    app = Path("/opt/zeronet/app")
    if "--apply-patch" in sys.argv:
        installer = Path("/review/docker/scripts/install-zeronet.sh").read_text()
        patch = installer.split("<<'INNER_PATH_PATCH'\n", 1)[1].split("\nINNER_PATH_PATCH", 1)[0]
        subprocess.run(
            [sys.executable, "-", str(app / "src/Content/ContentManager.py")],
            input=patch, text=True, check=True,
        )
    os.chdir(app)
    sys.path[:0] = [str(app), str(app / "src"), str(app / "src/lib")]
    sys.argv = ["zeronet.py", "--no-bootstrap", "--offline"]
    from src.Config import config
    sys.modules["Config"] = sys.modules["src.Config"]
    config.parse()
    from Content.ContentManager import ContentManager, VerifyError
    from Crypt import CryptBitcoin

    private_key = CryptBitcoin.newPrivatekey()
    address = CryptBitcoin.privatekeyToAddress(private_key)

    def manager():
        instance = ContentManager.__new__(ContentManager)
        instance.contents = {}
        instance.log = Mock()
        instance.isArchived = Mock(return_value=False)
        instance.site = SimpleNamespace(
            address=address, settings={"size": 123, "size_optional": 0},
            getSizeLimit=lambda: 1,
            worker_manager=SimpleNamespace(
                tasks=SimpleNamespace(findTask=Mock(return_value=None)), failTask=Mock()
            ),
        )
        return instance

    def signed(**changes):
        content = {
            "files": {}, "address": address, "inner_path": "content.json",
            "modified": 1, **changes,
        }
        content["signs"] = {address: CryptBitcoin.sign(json.dumps(content, sort_keys=True), private_key)}
        return content

    def rejected(content, expected):
        try:
            manager().verifyFile("content.json", content)
        except VerifyError as error:
            assert expected in str(error), str(error)
        else:
            raise AssertionError("invalid manifest was accepted")

    valid = signed()
    assert manager().verifyFile("content.json", copy.deepcopy(valid)) is True
    tampered = copy.deepcopy(valid)
    tampered["description"] = "modified after signing"
    rejected(tampered, "Valid signs: 0/1")
    unsigned = copy.deepcopy(valid)
    del unsigned["signs"]
    rejected(unsigned, "Not signed")
    rejected(signed(inner_path="other/content.json"), "Wrong inner_path")
    rejected(signed(description="x" * 1024 * 1024), "Content too large")
    print("PASS: real signatures accepted; tampered, unsigned, wrong-path and oversized manifests rejected")


if __name__ == "__main__":
    main()
