# The `formatdetect`subpackage



The `formatdetect` subpackage provides classes to get information about the format of data streams.

Based on a abstract FormatDetector class, we have different Detector Implementations:

  - [SiegfriedDetector](siegfrieddetector.md) is the currently used default Detector. 
    It is based on the the Siegfried format detector Magika format detection library. 
    We strongly suggest to use this detector, as it is based on the PRONOM format registry. 
  - [MagikaDetector](magikadetector.md) is based on the Google Magika format detection library. 
  - [MinimalDetector](MinimalDetector) is a naive detector based on mimetypes

Each detector provides a `guess_file_type()` method, which returns a FormatInfo object.




