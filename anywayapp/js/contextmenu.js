/*
new ContextMenuView({ items : { [ icon : "blat", text : "blat", callback : function() {} ] } })
 */
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
			$("<li>").appendTo(this.$el)
				.append($("<span/>", { class : "icon-" + this.items[i].icon}))
				.append($("<span/>", {class : "text", text : " " + this.items[i].text }));
		}

		$(document.body).append(this.$el);

		this.event = e;
		/*
		this.$el.css({
			top : e.pixel.y + this.$el.offset().top,
			left : e.pixel.x + this.$el.offset().left
		});
		*/
		this.$el.css({
			top : e.pixel.y + 40,
			left : e.pixel.x - 400
		});


		$(document.body).one("contextmenu click", _.bind(this.remove, this));

		return this;
	},
	remove : function() {
		this.$el.remove();
	},
	clickItem : function(e) {
		this.items[$(e.target).index()].callback($(e.target).index(), this.event);
	}
});

