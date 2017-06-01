angular.module('app.timelogs.services').factory('TimeLog', TimeLog);

TimeLog.$inject = ['$resource', 'HLResource'];
function TimeLog($resource, HLResource) {
    var _timelog = $resource(
        '/api/:model/:id/timelogs/',
        null,
        {
            query: {
                method: 'GET',
                params: {
                    model: '@model',
                    id: '@id',
                },
            },
            update: {
                method: 'PATCH',
                params: {
                    id: '@id',
                },
            },
            patch: {
                method: 'PATCH',
                params: {
                    id: '@id',
                },
            },
        }
    );

    _timelog.updateModel = updateModel;

    /////////

    function updateModel(data, field, timelogObject) {
        const args = HLResource.createArgs(data, field, timelogObject);

        let patchPromise = HLResource.patch('Timelog', args).$promise;

        return patchPromise;
    }

    return _timelog;
}
