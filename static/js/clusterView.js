var ClusterView = Backbone.View.extend({
	events : {

	},
	initialize : function(options) {
		this.map = options.map;
	},
	render : function() {
        app.clusterer.addCluster(this.model.get("latitude"), this.model.get("longitude"), this.model.get("size"));

        return this;
    }
});
