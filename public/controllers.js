angular.module('mainapp.controllers', []);
angular.module('mainapp.controllers').
controller('defaultController', ['$scope', '$http','mySocket','$window',
  function($scope, $http, mySocket, $window){
    var polarToCartesian = function(centerX, centerY, radius, angleInDegrees) {
      var angleInRadians = (angleInDegrees-90) * Math.PI / 180.0;
      return {x: centerX + (radius * Math.cos(angleInRadians)),
              y: centerY + (radius * Math.sin(angleInRadians))};
    }
    $scope.describeArc = function(x, y, radius, startAngle, endAngle){
      var start = polarToCartesian(x, y, radius, endAngle);
      var end = polarToCartesian(x, y, radius, startAngle);
      var largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
      var d = [
        "M", start.x, start.y, 
        "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
      ].join(" ");
      return d;       
    };
    var w = $window.innerWidth-100
    var h = $window.innerHeight
    $scope.sensors = []
    var colors = ["#e41a1c","#377eb8","#4daf4a","#984ea3"]
    mySocket.onMessage(function(message){
      msg = JSON.parse(message.data)
      console.log('msg: ', msg)
      var _id = msg['_id']
      var batt = msg['battery']
      var status = msg['status']
      var neighbour = msg['neighbour']
      var num_sensors = $scope.sensors.length
      var spacing = 400
      var level = Math.min(359, Math.max(batt*360/5,5))
      var percent = Math.round(100*batt/5)
      $scope.sensors[_id] = {'x':200+(spacing*_id), 'y': 200,'batt_percent':percent,
                              'status':status,'neighbour':neighbour, 'battery':level,'c':colors[_id], '_id':_id}
  })
}])