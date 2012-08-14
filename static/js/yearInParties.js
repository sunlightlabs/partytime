var chart1; // globally available
$(document).ready(function() {
      chart1 = new Highcharts.Chart({
         chart: {
            renderTo: 'yearInParties',
            type: 'area'
         },
         title: {
            text: 'Fruit Consumption'
         },
         xAxis: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',]
         },
         yAxis: {
            title: {
               text: 'Fruit eaten'
            }
         },
         series: [{
            name: 'Jane',
            data: [10, 15, 7, 23, 50, 14, 76, 83, 95, 61, 105, 13,]
         }]

      });
   });