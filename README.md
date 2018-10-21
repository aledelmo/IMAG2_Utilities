# IMAG2_Utilities
Stand-alone utilities scripts

## Contents

In this repository you can find a collection of various plug-in developed for
general use applications.

This tools can be considered complementary to the other repositories belonging to the IMAG2 framework.

### DICOM anonymizer
Given an existing folder this tool proceed to anonymize any DICOM files, removing all the sensible information
and making them ready to be shared and stored without any potential security risk.

The anonymization process progress iteratively and is extended to all the subdirectories of the main folder.

Attention: this tool has been tested and applied to data obtained from a General Electrics MRI scanner. While the 
process will still work for any DICOM series, it is possible
that some key fields will be deleted if images from different manufactors are used (notably the diffusion encoding parameters).

To use the script from a terminal write:
```sh
$ python DICOM_anonymizer.py <folder>
```

### Diffusion DICOM preprocessing

Initial test version for the automation of diffusion image denoising and preprocessing. A more updated pipeline
is now integrated in the [DiffusionPelvis] plug-in.

To use the script from a terminal write:
```sh
$ python -m canny.py <image_filepath>
```

Additional command line flags:

| short flag | long flag | Action |
| ------ | ------ | ------ |
| ```-m <filepath>``` | ```--mask <filepath>``` | Restrict operation to the selected binary mask |
| ```-n <name_string>``` | ```--basename <name_string>``` | Basename of the output processed volume |
| ```-q``` | ```--quiet``` | No message are printed to screen |

### Tractogram format converter
Convert a fiber tract file between the following formats: .tck, .trk, .vtk, .vtp, .xml

The conversion can is supported in both senses and for all the combinations. The original file
does not get eliminated. The converted output assumes the name of the input, with a different extension.

To use the script from a terminal write:
```sh
$ python tracto_converter.py <tractogram_filepath> <new_format>
```

Example:
```sh
$ python tracto_converter.py ~/Desktop/tractogram.tck vtk
```

### Canny filter

Interactive edge detector filter following the Canny approach.

Use the first slice to navigate through the axial slices of the image and the other two to vary the two
threshold required by the algorithm.

Supporting the NRRD file format.

To use the script from a terminal write:
```sh
$ python -m canny.py <image_filepath>
```

Example:
```sh
$ python tracto_converter.py ~/Desktop/coroT2Cube.nrrd
```

## Other repositories

These scripts serves as support for different tools. They can be complemented by:
* [3DSlicer Plug-ins]: segmentation and diffusion extension for 3DSlicer
* [PQL]: the first ever method for the segmentation of pelvic tractograms.
* [Tractography Metrics]: tool for the analysis of fiber bundles.
* [Vessel Segmentation]: deep-learning based approach for the automatic recognition of veins and arteries.
* [IMAG2 Website]: completely redesigned team website (<https://aledelmo.000webhostapp.com>)


[//]: #
   [3DSlicer Plug-ins]: <https://github.com/aledelmo/3DSlicer_Plugins>
   [PQL]: <https://github.com/aledelmo/PQL>
   [Tractography Metrics]: <https://github.com/aledelmo/TractographyMetrics>
   [Vessel Segmentation]: <https://github.com/aledelmo/VesselsSegmentation>
   [IMAG2 Utilities]: <https://github.com/aledelmo/IMAG2_Utilities>
   [IMAG2 Website]: <https://github.com/aledelmo/IMAG2_Website>
   [DiffusionPelvis]: <https://github.com/aledelmo/3DSlicer_Plugins/tree/master/DiffusionPelvis>