var fs = require("fs");
require("/Users/ron/Dropbox/Ron/src/anyway/anywayapp/js/libs/js-itm.js");
var data = JSON.parse(fs.readFileSync("coordinates.js"));

var results = [];
for (var i = 0; i < data.length; i++) {
	results.push(JSITM.itm2gps(data[i]));
}

console.log(JSON.stringify(results));