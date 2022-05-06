# Med Utils

Medical imaging utility scripts. Anonymization, Converters, Scores.

![intro](https://i.imgur.com/xheDkcR.png)

### DICOM Anonymization

Given an existing folder, this tool proceeds to anonymize any DICOM files, removing all the sensible information
and making them ready to be shared and stored without any potential security risk.

The anonymization process progress iteratively and is extended to all the subdirectories of the main folder.

Attention: this tool has been tested on data obtained from a General Electrics MRI scanner. While the 
script will still work for any DICOM series, it may happen that some key fields will be deleted with images from
different manufactures are used (notably the diffusion encoding parameters).

Use the script as a command line tool. Anonymization is in-place:
```sh
$ python DICOM_anonymizer.py <folder>
```

### Tractography Converter

Convert a fiber tract file between the following formats: .tck, .trk, .vtk, .vtp, .xml

The conversion can is supported in both senses and for all the combinations. The original file
does not get eliminated. The converted output assumes the name of the input, with a different extension.

Use the script as a command line tool:
```shell
$ python tracto_converter.py <tractogram_filepath> <new_format>
```
Example:
```sh
$ python tracto_converter.py tracto.tck vtk
```

### Dice Score & IOU

Sørensen–Dice coefficient and IOU coefficient computation between two binary masks.

DSC = 2 * TP / (2 * TP + FP + FN)
IOU = TP / (TP + FP + FN)

Implementation as 3D Slicer plug-in.

## Contacts

For any inquiries please contact: 
[Alessandro Delmonte](https://aledelmo.github.io) @ [alessandro.delmonte@institutimagine.org](mailto:alessandro.delmonte@institutimagine.org)

## License

This project is licensed under the [Apache License 2.0](LICENSE) - see the [LICENSE](LICENSE) file for
details