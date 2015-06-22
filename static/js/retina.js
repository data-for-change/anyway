var isRetina = (
    window.devicePixelRatio > 1 ||
    (window.matchMedia && window.matchMedia("(-webkit-min-device-pixel-ratio: 1.5),(-moz-min-device-pixel-ratio: 1.5),(min-device-pixel-ratio: 1.5)").matches)
);

if(isRetina){
    function addRetinaSuffix(url){
        return url.replace(/(^.*)(\.png)$/gi,function switchFunction(x,y1,y2){return y1+"@2x"+y2;});
    }

    for (var icon in ICONS){
        for (var i in ICONS[icon]){            
            ICONS[icon][i] = addRetinaSuffix(ICONS[icon][i]);
        }
    }
    for (var icon in MULTIPLE_ICONS){
        MULTIPLE_ICONS[icon] = addRetinaSuffix(MULTIPLE_ICONS[icon]);
    }
    USER_LOCATION_ICON = addRetinaSuffix(USER_LOCATION_ICON);
    DISCUSSION_ICON = addRetinaSuffix(DISCUSSION_ICON);
}