// Set the custom overlay object's prototype to a new instance
// of OverlayView. In effect, this will subclass the overlay class therefore
// it's simpler to load the API synchronously, using
// google.maps.event.addDomListener().
// Note that we set the prototype to an instance, rather than the
// parent class itself, because we do not wish to modify the parent class.

ContextMenuOverlay.prototype = new google.maps.OverlayView();

/** @constructor */
function ContextMenuOverlay(map, contextMenuView, e) {

  // Initialize all properties.
  this.map_ = map;
  this.contextMenuView = contextMenuView;
  this.e = e;

  // Explicitly call setMap on this overlay.
  this.setMap(map);
}

/**
 * onAdd is called when the map's panes are ready and the overlay has been
 * added to the map.
 */
ContextMenuOverlay.prototype.onAdd = function() { debugger;};

ContextMenuOverlay.prototype.draw = function() {
    debugger;
    this.contextMenuView.render(this.e);
};

// The onRemove() method will be called automatically from the API if
// we ever set the overlay's map property to 'null'.
ContextMenuOverlay.prototype.onRemove = function() { };


/* ------------------------------------------------------------ */
window.ContextMenuView = Backbone.View.extend({
    tagName: "ul",
    className: "context-menu",
    initialize: function(options) {
        this.items = options.items;
    },
    events : {
        "click li" : "clickItem"
    },
    render: function(e) {
        debugger;
        for (var i = 0; i < this.items.length; i++) {
            $('<li data-toggle="modal" href="' + this.items[i].href + '" class="btn">')
            .appendTo(this.$el)
            .append($("<span/>", {class: "icon-" + this.items[i].icon}))
            .append($("<span/>", {class: "text", text: " " + this.items[i].text }));
        }

        this.$el.css({
            top : e.pixel.y + 40,
            left : e.pixel.x
        });

        //remove old context menu
        $(document.body).remove('.context-menu');

        $(document.body).append(this.$el);
        $(document.body).one("contextmenu click", _.bind(this.remove, this));

        return this;
    },
    remove : function() {
        this.$el.remove();
    },
    clickItem : function(e) {
        this.items[$(e.currentTarget).index()].callback();
    }
});

