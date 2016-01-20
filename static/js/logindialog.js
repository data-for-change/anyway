/**
 * Created by Avik on 28-Dec-15.
 */
var LoginDialog = Backbone.View.extend({
    className: "login-dialog",
    events: {
        "submit": "submit",
        "click .close-button": "close"
    },
    render: function() {
        this.$el.append($("#login-dialog-template").html());
        $(document.body).append(this.$el);
        this.modal = this.$el.find(".modal");
        this.modal.modal("show");
        return this;
    },
    close: function() {
        this.modal.modal("hide");
    },
    submit: function() {
        this.close();
    }
});