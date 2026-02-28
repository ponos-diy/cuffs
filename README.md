# Cuffs

Generate custom-sized cuffs which can be mounted on extruded aluminum profiles.

Visit the [interactive customizer](https://ponos-diy.github.io/cuffs) to configure your own set.

## Used libraries
This project uses the following libraries:
* [OpenSWebCAD](https://github.com/hephaisto/openswebcad2), a wrapper for the other libraries (MIT, included)
* [OpenSCAD-WASM](https://github.com/openscad/openscad-wasm), a web-assembly port of OpenSCAD (GPL 2.0, [included](./openscad-wasm/LICENSE))
* [Pyodide](https://pyodide.org) to compile the python generation code to WASM (Mozilla Public License 2.0, referenced)
* [bootstrap](https://getbootstrap.com) to style the input widgets (MIT, referenced)
* [kowacsv/Online3DViewer](https://github.com/kovacsv/Online3DViewer) to display the generated files (MIT, [included](./o3dv/o3dv.license.md))

## License
The cuff repo is licensed as MIT.
The inclusion of GPL-libraries will probably also "infect" this project, so if you are concerned about that, you should probably distribute the corresponding libraries separately.

