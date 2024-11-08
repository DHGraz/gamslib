"""Handle project configuration.

The projectconfiguration package contains the classes and functions to 
manage the configuration of a GAMS project.

It tries to find a configuration, validates the configuration and provides
all configuration inline tables as Python objects.
"""

from .configuration import Configuration, load_configuration
__all__ = ["Configuration", "load_configuration"]
