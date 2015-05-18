MarkerClusterer.prototype.addCluster = function (clat, clng, csize) {
    this.setZoomOnClick(false);
    if (typeof this.aAddClusterIcons == "undefined") {
        this.aAddClusterIcons = [];
    }

    this.activeMap_ = this.getMap();
    var clusterlocation = new google.maps.LatLng(clat, clng);
    var CI = new ClusterIcon(new Cluster(this));
    var index = 0;
    var dv = csize;
    while (dv !== 0) {
        dv = parseInt(dv / 10, 10);
        index++;
    }
    var style = this.styles_[index - 1];
    $.extend(CI, {
        sums_: {text: csize, index: index},
        url_: style['url'],
        width_: style['width'],
        height_: style['height'],
        anchorIcon_: [clat, clng],
        anchorText_: [0, 0],
        backgroundPosition_: '0 0'
    });
    CI.setCenter(clusterlocation);
    CI.setMap(this.activeMap_);
    CI.show();

    this.aAddClusterIcons.push(CI);
};
MarkerClusterer.prototype.removeClusters = function (clat, clng, csize) {
    if (typeof this.aAddClusterIcons == "undefined") {
        this.aAddClusterIcons = [];
    }

    $.each(this.aAddClusterIcons, function (iIndex, oObj) {
        oObj.onRemove();
    });
    this.aAddClusterIcons = [];
};