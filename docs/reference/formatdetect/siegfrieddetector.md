# The `SiegfriedDetector` class

This is the suggested and default Detector Class. 

Usage:

```python
from gamslib.formatdetect.siegfrieddetector import Siegfriedetector as Detector

detector = Detector()
format = detector.guess_file_type('foo/bar.xml')
```

::: gamslib.formatdetect.SiegfriedDetector