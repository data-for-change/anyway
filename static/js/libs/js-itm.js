/**
 * @fileOverview js-itm: a Javascript library for converting between Israel Transverse Mercator (ITM) and GPS (WGS84) coordinates.<p>
 * <a href="http://code.google.com/p/js-itm/">http://code.google.com/p/js-itm/</a>
 * @author Udi Oron (udioron at g mail dot com)
 * @author forked from <a href="http://www.nearby.org.uk/tests/GeoTools.html">GeoTools</a> by Paul Dixon
 * @copyright <a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>
 * @version 0.1.1 ($Rev: 9 $ $Date: 2010-04-18 13:33:07 -0700 (Sun, 18 Apr 2010) $)
 */

/**
 * Parent namespace for the entire library
 * @namespace
 */
JSITM = {};

/**************************************************************/

/**
 * Creates a new LatLng.
 * 
 * @class holds geographic coordinates measured in degrees.<br/>
 * <a href="http://en.wikipedia.org/wiki/Geographic_coordinate">http://en.wikipedia.org/wiki/Geographic_coordinate</a>
 *
 * @constructor
 * @param {Number} lat latitude in degrees ( http://en.wikipedia.org/wiki/Latitude )
 * @param {Number} lng longtitude in degrees ( http://en.wikipedia.org/wiki/Longitude )
 * @param {Number} alt altitude in meters above the uesd geoid surface - this was not used or tested - please keep this always 0.
 * @param {Number} precision number of digits after the decimal point, used in printout. see toString().
 */
JSITM.LatLng = function(lat, lng, alt, precision){
    this.lat = lat;
    this.lng = lng;
    this.alt = alt || 0;
    this.precision = precision || 5;
}

/**
 * Returns Latlng as string, using the defined preccision
 * @return {String}
 */
JSITM.LatLng.prototype.toString = function(){

    function round(n, precision){
        var m = Math.pow(10, precision || 0);
        return Math.round(n * m) / m;
    }
    
    return round(this.lat, this.precision) + " " + round(this.lng, this.precision);
}

/**
 * Creates a new LatLng by converting coordinates from a source ellipsoid to a target one. <p>
 * This process involves:<p>
 *   1. converting the angular latlng to cartesian coordinates using latLngToPoint()<p>
 *   2. translating the XYZ coordinates using a translation, with special values supplied to this translation.<p>
 *   3. converting the translated XYZ coords back to a new angular LatLng<p>
 *<p>
 *  for example refer to {@link JSITM.itm2gps}
 *
 * @param {JSITM.Ellipsoid} from source elli
 * @param {JSITM.Ellipsoid} to
 * @param {JSITM.Translation} translation
 * @return {JSITM.LatLng}
 */
JSITM.LatLng.prototype.convertGrid = function(from, to, translation){

    var point = from.latLngToPoint(this, 0);
    
    //removed 7 point Helmert translation (not needed in Israel's grids)
    var translated = translation.translate(point);
    
    return to.pointToLatLng(translated);
}

/**
 * Parses latitude and longtitude in a string into a new Latlng
 * @param {String} s
 * @return {JSITM.LatLng}
 */
JSITM.latlngFromString = function(s) {
    var pattern = new RegExp("^(-?\\d+(?:\\.\\d*)?)(?:(?:\\s*[:,]?\\s*)|\\s+)(-?\\d+(?:\\.\\d*)?)$", "i")
    var latlng = s.match(pattern);
    if (latlng) {
        var lat = parseFloat(latlng[1], 10);
        var lng = parseFloat(latlng[2], 10);
        return new JSITM.LatLng(lat, lng);
    }

	throw ("could not parse latlng")
}

/**************************************************************/

/**
 * Creates a new Point.
 * @class holds 2D/3D cartesian coordinates.
 * 
 * @constructor
 * @param {Number} x
 * @param {Number} y
 * @param {Number} z
 * @return {JSITM.Point}
 */
JSITM.Point = function(x, y, z){
    this.y = y;
    this.x = x;
    this.z = z || 0;
}

/**
 * Returns a string containing the Point coordinates in meters
 * @return {String}
 */
JSITM.Point.prototype.toString = function(){
	
    return Math.round(this.x) + " " + Math.round(this.y);
}


/**************************************************************/

/**
 * Creates a new Translation.
 * <p>
 * (Helmert translation were depracted since they are not used in the ITM - feel free to add them back from geotools if you need them! :-) )
 * 
 * @constructor 
 * @param {Number} dx
 * @param {Number} dy
 * @param {Number} dz
 */
JSITM.Translation = function(dx, dy, dz){
    this.dx = dx;
    this.dy = dy;
    this.dz = dz;
}

/**
 * Return a new translated Point. (Original point kept intact)
 *
 * @param {JSITM.Point} point original point.
 * @return {JSITM.Point}
 */
JSITM.Translation.prototype.translate = function(point){
    return new JSITM.Point(point.x + this.dx, point.y + this.dy, point.z + this.dz);
}

/**
 * Returns an new Translation with inverse values.
 * @return {JSITM.Translation}
 */
JSITM.Translation.prototype.inverse = function(){
    return new JSITM.Translation(-this.dx, -this.dy, -this.dz);
}

/**************************************************************/

/**
 * Creates a new Ellipsoid.<p>
 * for more info see <a href="http://en.wikipedia.org/wiki/Reference_ellipsoid">http://en.wikipedia.org/wiki/Reference_ellipsoid</a>
 *
 * @constructor
 * @param {Number} a length of the equatorial radius (the semi-major axis) in meters
 * @param {Number} b length of the polar radius (the semi-minor axis) in meters
 */
JSITM.Ellipsoid = function(a, b){
    this.a = a;
    this.b = b;
    
    // Compute eccentricity squared
    this.e2 = (Math.pow(a, 2) - Math.pow(b, 2)) / Math.pow(a, 2);
    
}

/**************************************************************/

/**
 * Creates a new LatLng containing an angular representation of a cartesian Point on the surface of the Ellipsoid.
 *
 * @param {JSITM.Point} point
 * @return {JSITM.LatLng}
 */
JSITM.Ellipsoid.prototype.pointToLatLng = function(point){

    var RootXYSqr = Math.sqrt(Math.pow(point.x, 2) + Math.pow(point.y, 2));
    
    var radlat1 = Math.atan2(point.z, (RootXYSqr * (1 - this.e2)));
    
    do {
        var V = this.a / (Math.sqrt(1 - (this.e2 * Math.pow(Math.sin(radlat1), 2))));
        var radlat2 = Math.atan2((point.z + (this.e2 * V * (Math.sin(radlat1)))), RootXYSqr);
        if (Math.abs(radlat1 - radlat2) > 0.000000001) {
            radlat1 = radlat2;
        }
        else {
            break;
        }
    }
    while (true);
    
    var lat = radlat2 * (180 / Math.PI);
    var lng = Math.atan2(point.y, point.x) * (180 / Math.PI);
    
    return new JSITM.LatLng(lat, lng);
}

/**
 * Creates a new Point object containing a cartesian representation of an angular LatLng on the surface of the Ellipsoid.
 *
 * @param {JSITM.LatLng} latlng
 * @return {JSITM.Point}
 */
JSITM.Ellipsoid.prototype.latLngToPoint = function(latlng){
    // Convert angle measures to radians
    var radlat = latlng.lat * (Math.PI / 180);
    var radlng = latlng.lng * (Math.PI / 180);
    
    // Compute nu
    var V = this.a / (Math.sqrt(1 - (this.e2 * (Math.pow(Math.sin(radlat), 2)))));
    
    // Compute XYZ
    var x = (V + latlng.alt) * (Math.cos(radlat)) * (Math.cos(radlng));
    var y = (V + latlng.alt) * (Math.cos(radlat)) * (Math.sin(radlng));
    var z = ((V * (1 - this.e2)) + latlng.alt) * (Math.sin(radlat));
    
    return new JSITM.Point(x, y, z);
}

/**
 * Cretaes a new TM (Transverse Mercator Projection).<br>
 * For more info see <a href="http://en.wikipedia.org/wiki/Transverse_Mercator">http://en.wikipedia.org/wiki/Transverse_Mercator</a>
 *
 * @constructor
 * @param {JSITM.Ellipsoid} reference ellipsoid
 * @param {Number} e0 eastings of false origin in meters
 * @param {Number} n0 northings of false origin in meters
 * @param {Number} f0 central meridian scale factor
 * @param {Number} lat0 latitude of false origin in decimal degrees.
 * @param {Number} lng0 longitude of false origin in decimal degrees.
 */
JSITM.TM = function(ellipsoid, e0, n0, f0, lat0, lng0){
    //eastings (e0) and northings (n0) of false origin in meters; _
    //central meridian scale factor (f0) and _
    //latitude (lat0) and longitude (lng0) of false origin in decimal degrees.
    
    this.ellipsoid = ellipsoid;
    this.e0 = e0;
    this.n0 = n0;
    this.f0 = f0;
    this.lat0 = lat0;
    this.lng0 = lng0;
    
    this.radlat0 = lat0 * (Math.PI / 180);
    this.radlng0 = lng0 * (Math.PI / 180);
    
    this.af0 = ellipsoid.a * f0;
    this.bf0 = ellipsoid.b * f0;
    this.e2 = (Math.pow(this.af0, 2) - Math.pow(this.bf0, 2)) / Math.pow(this.af0, 2);
    this.n = (this.af0 - this.bf0) / (this.af0 + this.bf0);
    this.n2 = this.n * this.n; //for optimizing and clarity of Marc()
    this.n3 = this.n2 * this.n; //for optimizing and clarity of Marc()
    
}

/**
 * Compute meridional arc
 * @private
 * @param {Number} radlat latitude of meridian in radians
 * @return {Number}
 */
JSITM.TM.prototype.Marc = function(radlat){
    
    return (
		this.bf0 * (
			((1 + this.n + ((5 / 4) * this.n2) + ((5 / 4) * this.n3)) * (radlat - this.radlat0)) - 
			(((3 * this.n) + (3 * this.n2) + ((21 / 8) * this.n3)) * (Math.sin(radlat - this.radlat0)) * (Math.cos(radlat + this.radlat0))) + 
			((((15 / 8) * this.n2) + ((15 / 8) * this.n3)) * (Math.sin(2 * (radlat - this.radlat0))) * (Math.cos(2 * (radlat + this.radlat0)))) - 
			(((35 / 24) * this.n3) * (Math.sin(3 * (radlat - this.radlat0))) * (Math.cos(3 * (radlat + this.radlat0))))
		)
	);
		

}

/**
 * Returns the  initial value for Latitude in radians.
 * @private
 * @param {Number} y northings of point
 * @return {Number}
 */
JSITM.TM.prototype.InitialLat = function(y){
  
    var radlat1 = ((y - this.n0) / this.af0) + this.radlat0;

    var M = this.Marc(radlat1);
    
    var radlat2 = ((y - this.n0 - M) / this.af0) + radlat1;
    
    while (Math.abs(y - this.n0 - M) > 0.00001) {
        radlat2 = ((y - this.n0 - M) / this.af0) + radlat1;
        M = this.Marc(radlat2);
        radlat1 = radlat2;
    }
    return radlat2;
}

/**
 * Un-project Transverse Mercator eastings and northings back to latitude and longtitude.
 * 
 * @param {JSITM.Point} point
 * @return {JSITM.LatLng} latitude and longtitude on the refernced ellipsoid's surface
 */

JSITM.TM.prototype.unproject = function(point){
    //
    //Input: - _
    
    //Compute Et
    var Et = point.x - this.e0;
    
    //Compute initial value for latitude (PHI) in radians
    var PHId = this.InitialLat(point.y);
    
    //Compute nu, rho and eta2 using value for PHId
    var nu = this.af0 / (Math.sqrt(1 - (this.e2 * (Math.pow(Math.sin(PHId), 2)))));
    var rho = (nu * (1 - this.e2)) / (1 - (this.e2 * Math.pow(Math.sin(PHId), 2)));
    var eta2 = (nu / rho) - 1;
    
    //Compute Latitude
    var VII = (Math.tan(PHId)) / (2 * rho * nu);
    var VIII = ((Math.tan(PHId)) / (24 * rho * Math.pow(nu, 3))) * (5 + (3 * Math.pow(Math.tan(PHId), 2)) + eta2 - (9 * eta2 * (Math.pow(Math.tan(PHId), 2))));
    var IX = (Math.tan(PHId) / (720 * rho * Math.pow(nu, 5))) * (61 + (90 * Math.pow(Math.tan(PHId), 2)) + (45 * (Math.pow(Math.tan(PHId), 4))));
    
    var lat = (180 / Math.PI) * (PHId - (Math.pow(Et, 2) * VII) + (Math.pow(Et, 4) * VIII) - (Math.pow(Et, 6) * IX));
    
    //Compute Longitude
    var X = (Math.pow(Math.cos(PHId), -1)) / nu;
    var XI = ((Math.pow(Math.cos(PHId), -1)) / (6 * Math.pow(nu, 3))) * ((nu / rho) + (2 * (Math.pow(Math.tan(PHId), 2))));
    var XII = ((Math.pow(Math.cos(PHId), -1)) / (120 * Math.pow(nu, 5))) * (5 + (28 * (Math.pow(Math.tan(PHId), 2))) + (24 * (Math.pow(Math.tan(PHId), 4))));
    var XIIA = ((Math.pow(Math.cos(PHId), -1)) / (5040 * Math.pow(nu, 7))) * (61 + (662 * (Math.pow(Math.tan(PHId), 2))) + (1320 * (Math.pow(Math.tan(PHId), 4))) + (720 * (Math.pow(Math.tan(PHId), 6))));
    
    var lng = (180 / Math.PI) * (this.radlng0 + (Et * X) - (Math.pow(Et, 3) * XI) + (Math.pow(Et, 5) * XII) - (Math.pow(Et, 7) * XIIA));
    
    var latlng = new JSITM.LatLng(lat, lng);
    
    return (latlng);
}


/**
 * Project Latitude and longitude to Transverse Mercator coordinates
 * @param {JSITM.LatLng} latitude and longtitude  to convert
 * @return {JSITM.Point} projected coordinates 
 */
JSITM.TM.prototype.project = function(latlng){
    // Convert angle measures to radians
    var RadPHI = latlng.lat * (Math.PI / 180);
    var RadLAM = latlng.lng * (Math.PI / 180);
    
    var nu = this.af0 / (Math.sqrt(1 - (this.e2 * Math.pow(Math.sin(RadPHI), 2))));
    var rho = (nu * (1 - this.e2)) / (1 - (this.e2 * Math.pow(Math.sin(RadPHI), 2)));
    var eta2 = (nu / rho) - 1;
    var p = RadLAM - this.radlng0;
    var M = this.Marc(RadPHI);
    
    var I = M + this.n0;
    var II = (nu / 2) * (Math.sin(RadPHI)) * (Math.cos(RadPHI));
    var III = ((nu / 24) * (Math.sin(RadPHI)) * (Math.pow(Math.cos(RadPHI), 3))) * (5 - (Math.pow(Math.tan(RadPHI), 2)) + (9 * eta2));
    var IIIA = ((nu / 720) * (Math.sin(RadPHI)) * (Math.pow(Math.cos(RadPHI), 5))) * (61 - (58 * (Math.pow(Math.tan(RadPHI), 2))) + (Math.pow(Math.tan(RadPHI), 4)));
    
    var y = I + (Math.pow(p, 2) * II) + (Math.pow(p, 4) * III) + (Math.pow(p, 6) * IIIA);
    
    var IV = nu * (Math.cos(RadPHI));
    var V = (nu / 6) * (Math.pow(Math.cos(RadPHI), 3)) * ((nu / rho) - (Math.pow(Math.tan(RadPHI), 2)));
    var VI = (nu / 120) * (Math.pow(Math.cos(RadPHI), 5)) * (5 - (18 * (Math.pow(Math.tan(RadPHI), 2))) + (Math.pow(Math.tan(RadPHI), 4)) + (14 * eta2) - (58 * (Math.pow(Math.tan(RadPHI), 2)) * eta2));
    
    var x = this.e0 + (p * IV) + (Math.pow(p, 3) * V) + (Math.pow(p, 5) * VI);
    
    return new JSITM.Point(x, y, 0)
}

/** Juicy part 1 ***************************************************************************/

/**
 * Ellipsoid for GRS80 (The refernce ellipsoid of ITM
 * @see http://en.wikipedia.org/wiki/GRS80
 * @type JSITM.Ellipsoid
 */
JSITM.GRS80 = new JSITM.Ellipsoid(6378137, 6356752.31414); 

/**
 * Ellipsoid for WGS84 (Used by GPS)
 * @see http://en.wikipedia.org/wiki/WGS80
 * @type JSITM.Ellipsoid
 */
JSITM.WGS84 = new JSITM.Ellipsoid(6378137, 6356752.314245);

/**
 * Simple Translation from GRS80 to WGS84
 * @see http://spatialreference.org/ref/epsg/2039/
 * @type JSITM.Translation
 */
JSITM.GRS80toWGS84 = new JSITM.Translation(-48, 55, 52); 

/**
 * Translation back from WGS84 to GRS80
 * @type JSITM.Translation
 */
JSITM.WGS84toGRS80 = JSITM.GRS80toWGS84.inverse();

/**
 * ITM (Israel Transverse Mercator) Projection 
 * @see http://en.wikipedia.org/wiki/Israeli_Transverse_Mercator
 * @type JSITM.TM
 */
JSITM.ITM = new JSITM.TM(JSITM.GRS80, 219529.58400, 626907.38999, 1.000006700000000, 31.734394, 35.204517);


/** Juicy part 2 ***************************************************************************/

/**
 * Converts a point to an ITM reference.
 * 
 * @example 
 *   JSITM.point2ItmRef(new JSITM.Point(200, 500)); // prints "200000500000"
 *   JSITM.point2ItmRef(new JSITM.Point(200, 500), 3); // prints "200500"
 * @param {JSITM.Point} point
 * @param {Number} precision 3=km, 4=100 meter, 5=decameter 6=meter.  optional, default is 6,
 * @return {String}
 */
JSITM.point2ItmRef = function(point, precision){

	function zeropad(num, len){
	    var str = new String(num);
	    while (str.length < len) {
	        str = '0' + str;
	    }
	    return str;
	}
	
	var p = precision || 6; 

    if (p < 3) 
        p = 3;
    if (p > 6) 
        p = 6;
    
    var div = Math.pow(10, (6 - p));
    var east = Math.round(point.x / div);
    var north = Math.round(point.y / div);
    return zeropad(east, p) + ' ' + zeropad(north, p);
	
}

/**
 * Parses an ITM reference and returns a Point object.<p>
 * throws an exception for invalid refernce!<p>
 * <p>
 * @example valid inputs:
 *  200500
 *  20005000
 *  2000000500000
 *  130:540
 *  131550:44000
 *  131 400
 *  210222 432111
 * 
 * @param {String} s
 * @return {JSITM.Point}
 */
JSITM.itmRef2Point = function(s){
    
    var precision;
    
    for (precision = 6; precision >= 3; precision--) {
        var pattern = new RegExp("^(\\d{" + precision + "})\\s*:?\\s*(\\d{" + precision + "})$", "i")
        var ref = s.match(pattern);
        if (ref) {
            if (precision > 0) {
                var mult = Math.pow(10, 6 - precision);
                var x = parseInt(ref[1], 10) * mult;
                var y = parseInt(ref[2], 10) * mult;
                return new JSITM.Point(x, y);
            }
        }
    }
    
	throw "Could not parse reference";
}


/** Juicy part 3 ***************************************************************************/

/**
 * Converts a Point on ITM to a LatLng on GPS 
 * @param {JSITM.Point} point
 * @return {JSITM.LatLng}
 */
JSITM.itm2gps = function(point){
    var latlng = this.ITM.unproject(point); //however, latlng is still on GRS80!
    return latlng.convertGrid(this.GRS80, this.WGS84, this.GRS80toWGS84);
}

/**
 * Converts a LatLng on GPS to a Point on ITM
 * @param {JSITM.LatLng} latlng
 * @return {JSITM.Point}
 */

JSITM.gps2itm = function(latlng){
    var wgs84 = latlng.convertGrid(this.WGS84, this.GRS80, this.WGS84toGRS80); //first convert to GRS80
    return this.ITM.project(wgs84);
}

/** Juicy part 4 ***************************************************************************/

/**
 * Converts an ITM grid refernece in 6, 8, 10 or 12 digits to a GPS angular Point instace
 * @param {String} s
 * @return {JSITM.Point}
 */
JSITM.itmRef2gps = function(s){
	var point = this.itmRef2Point(s);
	return this.itm2gps(point);
}

/**
 * Converts an ITM grid refernece in 6, 8, 10 or 12 digits to a GPS angular reference
 * @param {String} s
 * @return {String}
 */
JSITM.itmRef2gpsRef = function(s){
	return this.itmRef2gps(s).toString();
}

/**
 * Converts a GPS angular reference to an ITM LatLng instance
 * @param {String} s
 * @return {JSITM.LatLng} 
 */

JSITM.gpsRef2itm = function(s){
	var latlng = this.latlngFromString(s);
	return this.gps2itm(latlng);
}

/**
 * Converts a GPS angular reference to an ITM grid refernece in 6, 8, 10 or 12 digits
 * @param {String} s
 * @param {Number} precision 3=km, 4=100 meter, 5=decameter 6=meter. Optional.  Default value is 6=meter
 * @return {String} 
 */

JSITM.gpsRef2itmRef = function(s, precision){
	return this.point2ItmRef(this.gpsRef2itm(s), precision || 6);
}
