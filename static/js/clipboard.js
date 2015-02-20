$(document).ready(function(){
    var url = document.URL;

    $("#map_link").val(url);
    $("#iframe_link").html('<iframe src="' + url + '&map_only=true"></iframe>');

    $(".js-btn-copytoclipboard").on("click", function(){
        $("#" + $(this).data("copy")).select();
    });
});