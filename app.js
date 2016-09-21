var mainapp =  angular.module('mainapp', ['angularModalService','ngRoute','multiStepForm','angucomplete-alt', 'mainapp.services','mainapp.controllers']);
mainapp.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.
            when('/login',{
                islogin: true,
                templateUrl: 'static/partials/login.html',
            }).
            when('/signup',{
                islogin: true,
                templateUrl: 'static/partials/just_email.html',
                controller: 'campaign_signup'
            }).
            when('/thanks', {
                islogin: true,
                templateUrl: 'static/partials/thanks.html'
            }).
            when('/main', {
                templateUrl: 'static/partials/home.html',
                islogin: false
            }).
            when('/data', {
                controller: 'plaidController',
                templateUrl: 'static/partials/data.html',
                islogin: false
            }).
            when('/plaid',{
                islogin:true
            }). 
            when('/accept/:inviteId', {
                islogin:true,
                controller: 'joiningController',
                templateUrl: 'static/partials/access.html'
            }).
            when('/user/:userId', {
                controller: 'plaidgodController',
                templateUrl: 'static/partials/data.html',
                islogin: false
            }).
            when('/blog',{
                islogin: true,
                templateUrl: 'app/templates/blogindex.html',
            }).
            when('/install',{
                islogin: true,
                templateUrl: 'app/templates/install.html',
            }).
            when('/logout', {
                controller: 'logoutController',
                }).
            otherwise({
                redirectTo: '/signup'
                })
}]).
run(function ($rootScope, $location, $route,$window, AuthService) {
  $rootScope.$on('$routeChangeStart',
    function (event, next, current) {
      console.log('changing')
      AuthService.getUserStatus()
      .then(function(){
        if (!next.islogin && !AuthService.isLoggedIn()){
          //$route.reload();
          console.log('rerouting')
          var landingUrl = "https://" + $window.location.host + "#/signup";
          $window.location.href = landingUrl;
        }
      });
  });
});