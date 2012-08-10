var chart1; // globally available
$(document).ready(function() {
      chart1 = new Highcharts.Chart({
         chart: {
            renderTo: 'yearInParties',
            type: 'area'
         },
         title: {
            text: 'The Year In Parties'
         },
         xAxis: {
            categories: [{% for month in month_names%}'{{month.name}}'{% if forloop.last %}{% else %},{% endif %}{% endfor %}]
         },
         yAxis: {
            title: {
               text: 'Number'
            }
         },
         series: [{
            name: 'Parties',
            data: [{% for data in month_data%}{{data.count}}{% if forloop.last %}{% else %},{% endif %}{% endfor %}]
         }]

      });
   });