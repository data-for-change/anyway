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
        for (var i = 0; i < this.items.length; i++) {
            $('<li data-toggle="modal" href="' + this.items[i].href + '" class="btn">')
            .appendTo(this.$el)
            .append($("<span/>", {class: "icon-" + this.items[i].icon}))
            .append($("<span/>", {class: "text", text: " " + this.items[i].text }));
        }

        $(document.body).append(this.$el);

        this.event = e;

        this.$el.css({
            top : e.pixel.y + 40,
            left : e.pixel.x
        });

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

