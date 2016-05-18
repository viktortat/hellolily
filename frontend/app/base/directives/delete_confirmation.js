require('sweetalert2');

/**
 * Directive to show a confirmation box before deleting.
 */
angular.module('app.directives').directive('deleteConfirmation', deleteConfirmation);
function deleteConfirmation() {
    return {
        restrict: 'E',
        scope: {
            model: '@',
            object: '=',
            displayField: '@?',
            callback: '&?',
            buttonClass: '@?',
        },
        templateUrl: 'base/directives/delete_confirmation.html',
        controller: DeleteConfirmationController,
        controllerAs: 'vm',
        transclude: true,
        bindToController: true,
    };
}

DeleteConfirmationController.$inject = ['$state', 'HLMessages', 'HLResource'];
function DeleteConfirmationController($state, HLMessages, HLResource) {
    var vm = this;

    vm.openConfirmationModal = openConfirmationModal;

    activate();

    ////

    function activate() {
        if (!vm.buttonClass) {
            vm.buttonClass = '';
        }
    }

    function openConfirmationModal() {
        var name = '';

        if (vm.displayField) {
            name = vm.object[vm.displayField];
        } else if (vm.object.hasOwnProperty('name')) {
            name = vm.object.name;
        } else if (vm.object.hasOwnProperty('full_name')) {
            name = vm.object.full_name;
        }

        swal({
            title: HLMessages.alerts.delete.confirmTitle,
            html: sprintf(HLMessages.alerts.delete.confirmText, {name: name ? name : 'this ' + vm.model.toLowerCase()}),
            type: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#f3565d',
            confirmButtonText: HLMessages.alerts.delete.confirmButtonText,
            preConfirm: function() {
                swal.enableLoading();
                return HLResource.delete(vm.model, vm.object);
            },
        }).then(function(isConfirm) {
            if (isConfirm) {
                swal({
                    title: HLMessages.alerts.delete.successTitle,
                    html: sprintf(HLMessages.alerts.delete.successText, {model: vm.model.toLowerCase(), name: name}),
                    type: 'success',
                }).then(function() {
                    // In certain cases we want to call a function of another controller.
                    if (vm.callback) {
                        // Call the given function.
                        vm.callback();
                    } else {
                        // Otherwise just go to the parent state.
                        $state.go($state.current.parent);
                    }
                });
            }
        });
    }
}

