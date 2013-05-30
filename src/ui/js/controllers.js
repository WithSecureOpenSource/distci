'use strict';

function distciuijobscontroller($scope, $http) {
  $http.get('/distci/jobs').success(function(data) {
    $scope.jobs = data.jobs;
    $scope.jobs.sort();
  });
};


function distciuijobbuildscontroller($scope, $routeParams, $http) {
  $scope.jobid = $routeParams.jobid;

  $scope.update = function() {
    $http.get('/distci/jobs/' + $scope.jobid + '/builds').success(function(data) {
      $scope.builds = data.builds;
      $scope.builds.sort(function(a,b){return b-a});
    });
  }

  $scope.trigger = function() {
    $http.post('/distci/jobs/' + $scope.jobid + '/builds').success(function(data) {
    $scope.update();
    });
  }

  $scope.update()
};

function distciuijobbuildstatecontroller($scope, $routeParams, $http) {
  $scope.jobid = $routeParams.jobid;
  $scope.build = $routeParams.build;

  $http.get('/distci/jobs/' + $routeParams.jobid + '/builds/' + $routeParams.build).success(function(data) {
    $scope.state = data.state;
    $scope.artifacts = [];
    for (var key in data.state.artifacts) {
        $scope.artifacts.push({"id": key, "fullname": data.state.artifacts[key].join('/'), "filename": data.state.artifacts[key].pop()});
    }
    $scope.artifacts.sort(function(a,b) {
      if (a.name<b.name) return -1;
      if (a.name>b.name) return 1;
      return 0;
    });
  });
};
