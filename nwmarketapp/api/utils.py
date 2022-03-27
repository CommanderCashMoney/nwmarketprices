from constance import config


def check_version_compatibility(version: str) -> bool:
    try:
        major, minor, patch = [int(vn) for vn in version.split(".")]
    except ValueError:
        return False

    block_on_diff = config.BLOCK_LOGIN_ON_SCANNER_DIFF
    server_major, server_minor, server_patch = [int(vn) for vn in config.LATEST_SCANNER_VERSION.split(".")]
    major_diff = server_major - major != 0
    minor_diff = server_minor - minor != 0
    patch_diff = server_patch - patch != 0
    if block_on_diff == 3 and major_diff:  # major
        return False
    elif block_on_diff == 2 and (major_diff or minor_diff):
        return False
    elif block_on_diff == 1 and (major_diff or minor_diff or patch_diff):
        return False

    return True
