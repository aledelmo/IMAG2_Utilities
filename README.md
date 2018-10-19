# IMAG2_Utilities
Stand-alone utilities scripts

## Contents

In this repository you can find a collection of various plug-in developed for
general use applications.

This tools can be considered complementary to the other repositories.

### DICOM anonymizer

### Diffusion DICOM preprocessing

### Tractogram format converter
Convert a fiber tract file between the followinf formats: .tck, .trk, .vtk, .vtp, .vtp

The conversion can is supported in both senses and for all the combinations. The original file
does not get eliminated. The converted output assumes the name of the input, with a different extension.

To use the script from a terminal write:
```sh
$ python -m tracto_converter.py <tractogram_filepath> <new_format>
```

Example:
```sh
$ python -m tracto_converter.py ~/Desktop/tractogram.tck vtk
```


### Canny filter