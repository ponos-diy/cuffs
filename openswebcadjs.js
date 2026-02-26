import OpenSCAD from "./openscad-wasm/openscad.js";
import "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pyodide.js";

export async function main(){
	await loadOpenswebcad();
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
			new OV.Coord3D (-75.0, 100.0, 150.0),
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

async function getRequirements() {
	const response = await fetch("requirements.txt");
	if(!response.ok) {
		throw new Error("Failed to download requirements.txt");
	}
	const text = await response.text();
	return text.split(/r?\n/);
}

async function installPackages(pyodide) {
	await pyodide.loadPackage("micropip");
	const micropip = pyodide.pyimport("micropip");
	await downloadFile(pyodide, "requirements.txt");
	const requirements = await getRequirements();
	for (const r of requirements) {
		if(!r.trim())
			continue;
		console.log(`installing ${r}`);
		await micropip.install(r);
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
	await pyodide.runPythonAsync(`
import openswebcad
import model
openswebcad.createRenderer=createRenderer
openswebcad.createRendererSpinner=createRendererSpinner
openswebcad.createRendererSurrounding=createRendererSurrounding
openswebcad.run(model)
	`);
}

