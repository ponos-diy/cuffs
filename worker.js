import OpenSCAD from "./openscad-wasm/openscad.js";

onmessage = async (e) => {
	name = e.data.name
	console.log(`Start render ${name}`);
	let result = await render(name, e.data.scad_code)
	console.log(`End   render ${name}`);
	postMessage(result);
};

async function loadOpenscad(){
	console.log("initializing openscad");
	const instance = await OpenSCAD({noInitialRun: true});
	console.log("initialized openscad");
	return instance;
}


async function render(name, scad_code) {
	let openscad = await loadOpenscad();
	const out_file = "/"+name+".stl";
	const in_file = "/"+name+".scad";
	openscad.FS.writeFile(in_file, scad_code);
	console.log("running openscad");
	openscad.callMain([in_file, "--enable=manifold", "-o", out_file]);
	console.log("reading file");
	return {"name": name, "stl": openscad.FS.readFile(out_file)};
}
