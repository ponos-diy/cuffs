import OpenSCAD from "./openscad-wasm/openscad.js";
import "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pyodide.js";
import {packages} from "./packages.js";

export async function main(){
	await loadOpenswebcad();
}

async function loadOpenscad(){
	console.log("initializing openscad");
	const instance = await OpenSCAD({noInitialRun: true});
	console.log("initialized openscad");
	return instance;
}

export async function renderOpenscadToViewer(scad_code, name, viewer, download_link){
	let openscad = await loadOpenscad();
	const out_file = "/"+name+".stl";
	const in_file = "/"+name+".scad";
	const viewer_file = "/"+name+"_view.stl";
	console.log("generating file");
	openscad.FS.writeFile(in_file, scad_code);
	console.log("running openscad");
	openscad.callMain([in_file, "--enable=manifold", "-o", out_file]);
	console.log("reading file");
	const data = openscad.FS.readFile(out_file);
	console.log("writing viewer file");
	const viewer_fp = new File([data], viewer_file, {});

	console.assert(download_link);
	download_link.href = URL.createObjectURL(new Blob([data], {type: "application/octet-stream"}), null);
	download_link.download = name + ".stl"

	console.log("loading model");
	viewer.LoadModelFromFileList([viewer_fp]);
	console.log("finished");
}


export function createRendererSurrounding(parentNode, name) {
	let border = document.createElement("div");
	border.classList.add("border");
	parentNode.appendChild(border);
	//let text = document.createElement("div");
	//text.innerHTML= name;
	//border.appendChild(text);
	let container = document.createElement("div");
	border.appendChild(container);
	return container;
}

export function createRendererSpinner(parentNode) {
	let node = document.createElement("div");
	node.classList.add("spinner-border");
	//node.hidden = true;
	parentNode.appendChild(node);
	return node;
}

export function createRenderer(parentNode) {
	return new OV.EmbeddedViewer (parentNode, {
		camera : new OV.Camera (
			new OV.Coord3D (-1.5, 2.0, 3.0),
			new OV.Coord3D (0.0, 0.0, 0.0),
			new OV.Coord3D (0.0, 1.0, 0.0),
			45.0
		),
		backgroundColor : new OV.RGBAColor (255, 255, 255, 255),
		defaultColor : new OV.RGBColor (200, 200, 200),
		edgeSettings : new OV.EdgeSettings (false, new OV.RGBColor (0, 0, 0), 1),
	});
}

async function downloadFile(pyodide, filename) {
	await pyodide.runPythonAsync(`
from pyodide.http import pyfetch
response = await pyfetch("${filename}")
response.raise_for_status()
with open("${filename}", "wb") as f:
    f.write(await response.bytes())
`);
}

async function installPackages(pyodide) {
	await pyodide.loadPackage("micropip");
	const micropip = pyodide.pyimport("micropip");
	let ps = packages()
	for(const p of packages()) {
		console.log(`installing ${p}`);
		await micropip.install(p);
	}
}

async function loadOpenswebcad(openscad){
	let pyodide = await loadPyodide();
	await installPackages(pyodide);
	await downloadFile(pyodide, "openswebcad.py");
	await downloadFile(pyodide, "parse.py");
	await downloadFile(pyodide, "model.py");
	await downloadFile(pyodide, "util.py");
	pyodide.globals.set("createRendererSurrounding", createRendererSurrounding);
	pyodide.globals.set("createRenderer", createRenderer);
	pyodide.globals.set("createRendererSpinner", createRendererSpinner);
	pyodide.globals.set("renderOpenscadToViewer", renderOpenscadToViewer);
	await pyodide.runPythonAsync(`
import openswebcad
import model
openswebcad.createRenderer=createRenderer
openswebcad.createRendererSpinner=createRendererSpinner
openswebcad.createRendererSurrounding=createRendererSurrounding
openswebcad.renderOpenscadToViewer=renderOpenscadToViewer
openswebcad.run(model)
	`);
	//let openswebcad = pyodide.pyimport("openswebcad");
	//openswebcad.run(renderOpenscadToViewer, createRenderer);
}

