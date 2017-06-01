function TimeLogDisplayController() {
    let ctrl = this;

    ctrl.$onInit = () => {
        ctrl.formatHours();
    };

    ctrl.$onChanges = (changesObject) => {
        ctrl.timeLogs = changesObject.timeLogs.currentValue;
        ctrl.formatHours();
    };

    ctrl.formatHours = () => {
        let hoursLogged = ctrl.timeLogs.reduce((hours, timeLog) => {
            return hours + parseFloat(timeLog.hours_logged);
        }, 0);

        let hours = Math.floor(hoursLogged);
        let minutes = Math.round(hoursLogged % 1 * 60);

        ctrl.hoursLogged = {hours, minutes};
    };
}

angular.module('app.timelogs.directives').component('timeLogDisplay', {
    templateUrl: 'timelogs/directives/time_log_display.html',
    controller: TimeLogDisplayController,
    bindings: {
        timeLogs: '<',
    },
});
