# The `projectconfiguration` subpackage

The `projectconfiguration` submodule provides code to create and 
use configuration settings for GAMS projects.

The package provides a few useful functions: 

  - `get_configuration()`: Returns a (cached) Configuration object
  - `configuration_needs_update()`: Returns `True`, if the format of 
    the existing configuration is deprecated (e.g. because we have 
    added new fields)
  - `update_configuration()`: Updates the existing configuration by inserting 
    new fields from the new schema.  


Here is an example how to retrieve the configuration object:

```python
from gamslib import projectconfiguration

cfg = get_configuration()
```

Check the docstrings for more information!

## Here is what I have extracted from the docstrings:

::: gamslib.projectconfiguration
    options:
      filters: ["!^Configuration$"]
      members: