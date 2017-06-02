angular.module('app.dashboard.directives').directive('unassignedCases', unassignedCasesDirective);

function unassignedCasesDirective() {
    return {
        templateUrl: 'dashboard/directives/unassignedcases.html',
        controller: UnassignedCasesController,
        controllerAs: 'vm',
        bindToController: true,
        scope: {
            teams: '=',
        },
    };
}

UnassignedCasesController.$inject = ['$http', '$scope', '$state', '$timeout', 'Case', 'HLFilters', 'HLUtils', 'LocalStorage'];
function UnassignedCasesController($http, $scope, $state, $timeout, Case, HLFilters, HLUtils, LocalStorage) {
    var vm = this;

    vm.storageName = 'unassignedCasesForTeamWidget';
    vm.storage = new LocalStorage(vm.storageName);
    vm.storedFilterSpecialList = vm.storage.get('filterSpecialListSelected', null);
    vm.storedFilterList = vm.storage.get('filterListSelected', null);
    vm.highPrioCases = 0;
    vm.table = {
        order: vm.storage.get('order', {
            descending: true,
            column: 'created',  // string: current sorted column
        }),
        items: [],
    };
    vm.filterList = [];
    vm.filterSpecialList = [];

    vm.assignToMe = assignToMe;
    vm.updateTable = updateTable;

    activate();

    /////

    function activate() {
        $timeout(() => {
            let filterSpecialList = [{
                name: 'Unassigned',
                value: '_missing_:assigned_to_teams',
                selected: false,
                isSpecialFilter: true,
                separate: true,
            }];

            vm.teams.map((team) => {
                filterSpecialList.unshift({
                    name: team.name,
                    value: 'assigned_to_teams:' + team.id,
                    selected: team.selected,
                    isSpecialFilter: true,
                    separate: true,
                });
            });

            HLFilters.getStoredSelections(filterSpecialList, vm.storedFilterSpecialList);

            vm.filterSpecialList = filterSpecialList;

            Case.getCaseTypes((caseTypes) =>  {
                let filterList = [];

                angular.forEach(caseTypes, (caseType) => {
                    filterList.push({
                        name: caseType.name,
                        value: 'type.id:' + caseType.id,
                        selected: false,
                        isSpecialFilter: true,
                    });
                });

                HLFilters.getStoredSelections(filterList, vm.storedFilterList);

                vm.filterList = filterList;
            });

            _watchTable();
        }, 50);
    }

    function updateTable() {
        var i;
        var filterQuery = 'is_archived:false AND _missing_:assigned_to.id';

        HLUtils.blockUI('#unassignedCasesBlockTarget', true);

        if (vm.table.filterQuery) {
            filterQuery += ' AND ' + vm.table.filterQuery;
        }

        Case.getCases(vm.table.order.column, vm.table.order.descending, filterQuery).then(function(data) {
            vm.table.items = data.objects;
            vm.highPrioCases = 0;

            for (i in data.objects) {
                if (data.objects[i].priority === 3) {
                    vm.highPrioCases++;
                }
            }

            HLUtils.unblockUI('#unassignedCasesBlockTarget');
        });
    }

    function assignToMe(caseObj) {
        swal({
            text: sprintf(messages.alerts.assignTo.questionText, {type: 'case'}),
            type: 'question',
            showCancelButton: true,
        }).then(function(isConfirm) {
            if (isConfirm) {
                Case.patch({id: caseObj.id, assigned_to: currentUser.id}).$promise.then(function() {
                    var index = vm.table.items.indexOf(caseObj);
                    vm.table.items.splice(index, 1);

                    $state.reload();
                });
            }
        }).done();
    }

    function _watchTable() {
        $scope.$watchGroup(['vm.table.order.descending', 'vm.table.order.column'], function() {
            vm.storage.put('order', vm.table.order);
            updateTable();
        });
    }
}
