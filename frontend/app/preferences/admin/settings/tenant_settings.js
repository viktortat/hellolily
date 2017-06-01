angular.module('app.preferences').config(tenantSettings);

tenantSettings.$inject = ['$stateProvider'];
function tenantSettings($stateProvider) {
    $stateProvider.state('base.preferences.admin.settings', {
        url: '/settings',
        views: {
            '@base.preferences': {
                templateUrl: 'preferences/admin/settings/tenant_settings.html',
                controller: TenantSettingsController,
                controllerAs: 'vm',
            },
        },
        resolve: {
            tenant: ['Tenant', Tenant => {
                return Tenant.query({}).$promise;
            }],
        },
    });
}

angular.module('app.preferences').controller('TenantSettingsController', TenantSettingsController);

TenantSettingsController.$inject = ['$state', '$window', 'HLForms', 'Tenant', 'tenant'];
function TenantSettingsController($state, $window, HLForms, Tenant, tenant) {
    var vm = this;

    vm.tenant = tenant;

    vm.saveSettings = saveSettings;

    function saveSettings(form) {
        HLForms.blockUI();

        Tenant.patch(tenant).$promise.then(() => {
            toastr.success('I\'ve saved the settings for you!', 'Yay');
            $window.location.reload();
        }, error => {
            toastr.error('Uh oh, there seems to be a problem', 'Oops!');
            HLForms.setErrors(form, response.data);
        });
    }
}

