'use strict';

angular.module('distciui', []).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/jobs', {templateUrl: 'html/jobs.html', controller: 'distciuijobscontroller'});
    $routeProvider.when('/jobs/:jobid', {templateUrl: 'html/jobbuilds.html', controller: 'distciuijobbuildscontroller'});
    $routeProvider.when('/jobs/:jobid/builds/:build', {templateUrl: 'html/jobbuildstate.html', controller: 'distciuijobbuildstatecontroller'});
    $routeProvider.otherwise({redirectTo: '/jobs'});
  }]);
