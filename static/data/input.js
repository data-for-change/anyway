require("./js-itm.js");

process.stdin.on('readable', function() {
    var chunk = process.stdin.read();
    if (chunk !== null) {
        process.stdout.write(JSON.stringify(JSITM.itm2gps(JSON.parse(chunk))) + "\n");
    }
});

