odoo.define('thesis_design_database_manager.NotifyAll', function (require) {
    "use strict";

    var bus = require('bus.bus').bus;

    bus.add_channel('notify_all');
    bus.start_polling();

    bus.on('notification', this, function (notifications) {
        _.each(notifications, function (notification) {
            if (notification[0] === 'notify_all') {
                var message = notification[1];
                self.do_notify(message.params.title, message.params.message, message.params.sticky);
            }
        });
    });
});
