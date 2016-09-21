angular.module('mainapp.services',[])
angular.module('mainapp.services').factory('mySocket', function($websocket) {
      // Open a WebSocket connection
      var dataStream = $websocket('ws://127.0.0.1:8080/');
      return dataStream;
  }).
directive('barPlot', function () {

    // Create a link function
    function linkFunc(scope, element, attrs) {
    	attrs.$observe('flavor', function(flavor) {
        	scope.whichone = flavor;
        	console.log('scope: ',scope)
      });
        scope.$watch('whichone', function (plots) {
        	var toplot = JSON.parse(plots)
            var layout = {
              title: toplot.status,
              width: toplot.sensorw||300,
              height: toplot.sensorh||300,
              titlefont: {
                family: ('Helvetica'),
                size: 22,
                color: '#252525'
              },
              yaxis: {range: [0, 5],
                      showgrid: false},
              showlegend: false,
              plot_bgcolor: '#ffffff',
              paper_bgcolor: '#ffffff',
              bargap :0.75
          }
            Plotly.newPlot(element[0], toplot.data, layout, {displayModeBar: false});
        }, true);
    }

    // Return this function for linking ...
    return {
        link: linkFunc
    };
})