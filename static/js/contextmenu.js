window.ContextMenuView = Backbone.View.extend({
    tagName: "ul",
    className: "context-menu",
    initialize: function(options) {
        this.items = options.items;
        this.contextMenuOverlay = Object.create(google.maps.OverlayView.prototype);
        this.createContextMenuOverlay(options.map, options.e);
    },
    events : {
        "click li" : "clickItem"
    },
    render: function(e) {
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

        this.$el.appendTo('body');

        $(document.body).one("contextmenu click", _.bind(this.remove, this));

        return this;
    },
    remove : function() {

        this.$el.remove();
        this.contextMenuOverlay.setMap(null);
    },
    clickItem : function(e) {
        this.items[$(e.currentTarget).index()].callback();
    },

    createContextMenuOverlay: function(map, e){
        var me = this;
        
        /* Implement 3 must have functions of google.maps.OverlayView object */
        this.contextMenuOverlay.onAdd = function(){ }

        this.contextMenuOverlay.draw = function() { me.render(e); }

        this.contextMenuOverlay.onRemove = function() { }

        this.contextMenuOverlay.setMap(map);
    }
});

