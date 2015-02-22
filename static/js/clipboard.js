$(document).ready(function(){
    var url = document.URL,
        $map_link = $("#map_link"),
        $iframe_link = $("#iframe_link"),
        $embed_link = $("#js-embed-link");

    $embed_link.on("click", function(){
        url = document.URL;

        $map_link.val(url);
        $iframe_link.html('<iframe src="' + url + '&map_only=true"></iframe>');
    });


    $(".js-btn-copytoclipboard").on("click", function(){
        $("#" + $(this).data("copy")).select();
    });
});