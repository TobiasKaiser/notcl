# SPDX-FileCopyrightText: 2025 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from importlib.metadata import version, PackageNotFoundError

try:
    version = version("notcl")
except PackageNotFoundError:
    version = "unknown"
