var chart1; // globally available
$(document).ready(function() {
      chart1 = new Highcharts.Chart({
         chart: {
            renderTo: 'weekInParties',
            type: 'area'
         },
         title: {
            text: 'Fruit Consumption'
         },
         xAxis: {
            categories: ['6/25', '6/26', '6/27', '6/28', '6/29', '6/30', '7/01', '7/02', '7/03', '7/04', '7/05', '7/06', '7/07', '7/08', '7/09', '7/10', '7/11', '7/12', '7/13', '7/14',]
         },
         yAxis: {
            title: {
               text: 'Fruit eaten'
            }
         },
         series: [{
            name: 'Parties',
            data: [2, 5, 7, 0, 11, 4, 17, 3, 5, 3, 3, 7, 2, 5, 7, 0, 11, 4, 17, 3,]
         }]

      });
   });