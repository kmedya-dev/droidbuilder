# This file will define the abstract base class for all build system resolvers.
#
# The BaseResolver class will define the common interface that all concrete
# resolvers must implement. This will ensure that the main builder can
# interact with any resolver in a consistent way.
#
# The base class will likely have the following abstract methods:
#
# from abc import ABC, abstractmethod
#
# class BaseResolver(ABC):
#     def __init__(self, package_source_path, arch, ndk_api, install_dir, build_triplet, host_triplet, cflags, ldflags, cc, cxx, ar, ld, ranlib, strip, readelf):
#         self.package_source_path = package_source_path
#         # ... and so on for all parameters
#
#     @abstractmethod
#     def get_build_commands(self):
#         """Returns a dictionary of build commands."""
#         pass
#
# The dictionary would contain keys like 'pre_configure', 'configure', 'build', and 'install'.
#
# Concrete resolvers (e.g., CMakeResolver, MesonResolver) will inherit
# from this base class and provide the specific implementation for each method.
