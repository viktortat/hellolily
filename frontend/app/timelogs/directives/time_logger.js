let Duration = require('duration-js');

angular.module('app.timelogs.directives').directive('timeLogger', timeLogger);

function timeLogger() {
    return {
        restrict: 'E',
        scope: {
            object: '=',
            updateCallback: '&?',
            case: '<',
        },
        templateUrl: 'timelogs/directives/time_logger.html',
        controller: TimeLoggerController,
        controllerAs: 'vm',
        bindToController: true,
    };
}

TimeLoggerController.$inject = ['$compile', '$scope', '$state', '$templateCache', 'TimeLog'];
function TimeLoggerController($compile, $scope, $state, $templateCache, TimeLog) {
    let vm = this;

    vm.currentUser = currentUser;
    vm.datepickerOptions = {
        startingDay: 1, // day 1 is Monday
    };
    vm.error = false;

    const timeLogDefaults = {
        gfk_content_type: vm.object.content_type,
        gfk_object_id: vm.object.id,
        date: moment().toDate(),
        case: vm.case.id,
        billable: currentUser.timeLogging.billingDefault,
    };

    vm.timeLog = Object.assign({}, timeLogDefaults);

    vm.logTime = logTime;
    vm.formatTime = formatTime;
    vm.openTimeLogModal = openTimeLogModal;

    function logTime() {
        vm.error = false;
        let hoursLogged = formatTime();

        if (hoursLogged) {
            vm.timeLog.hours_logged = hoursLogged;

            TimeLog.save(vm.timeLog).$promise.then(response => {
                // Because of the way Angular's $onChanges hook works we need
                // to assign a new reference for it to fire.
                let timeLogs = vm.object.timeLogs.slice();
                timeLogs.push(response);
                vm.object.timeLogs = timeLogs;

                vm.timeLog = Object.assign({}, timeLogDefaults);

                toastr.success('Your hours have been logged', 'Done!');
            }, response => {
                toastr.error('Uh oh, there seems to be a problem', 'Oops!');
            });
        } else {
            toastr.error('Uh oh, there seems to be a problem', 'Oops!');
            vm.error = true;
        }
    }

    function formatTime() {
        let time = vm.timeLog.time;
        vm.error = false;

        // No number in the given time, so invalid input.
        if (!/[0-9]/i.test(time)) {
            time = null;
        }

        if (time) {
            // No unit given so resort to default (hours).
            if (!/[a-z]/i.test(time)) {
                time += 'h';
            }

            time = time.replace(',', '.');

            try {
                time = new Duration(time);
            } catch (e) {
                // Invalid unit given, so incorrect input.
                time = null;
            } finally {
                time = (time.minutes() / 60).toFixed(3);
            }
        } else {
            vm.error = true;
        }

        return time;
    }

    function openTimeLogModal() {
        swal({
            title: messages.alerts.timeLog.modalTitle,
            html: $compile($templateCache.get('timelogs/controllers/time_logger.html'))($scope),
            showCloseButton: true,
        }).then(isConfirm => {
            // For some reason the datepicker doesn't get removed from the DOM when the SweetAlert is closed.
            // So just the datepicker as soon as the modal closes.
            let element = angular.element($('[uib-datepicker-popup-wrap]'));
            element.hide();

            if (isConfirm) {
                logTime();
            }
        }).done();
    }
}
