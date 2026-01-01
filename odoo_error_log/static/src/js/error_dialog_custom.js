odoo.define('odoo_error_log.error_dialog', function (require) {
    "use strict";
    
    var CrashManager = require('web.CrashManager');
    var CrashManagerDialog = CrashManager.ErrorDialog;
    var ajax = require('web.ajax'); // 引入ajax模块

    CrashManagerDialog.include({
        init: function (parent, options, error) {
            this._super.apply(this, arguments);
            this._logErrorToServer(error);
        },

        _logErrorToServer: function (error) {
            // 获取错误信息
            var errorData = {
                name: error.type || "Odoo Error", // 错误类型
                message: error.message || "Unknown Error", // 错误消息
                traceback: error.traceback || "No Traceback", // 错误堆栈
            };
            console.log(errorData.traceback);

            // 调用后端方法记录错误
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'error.log',
                method: 'create_and_send_email',
                args: [errorData], // 传递给后端的参数
                kwargs: {},
            }).then(function (result) {
                console.log("Error logged successfully on the server:", result);
            }).catch(function (error) {
                console.error("Failed to log error on the server:", error);
            });            
        },
    });

});