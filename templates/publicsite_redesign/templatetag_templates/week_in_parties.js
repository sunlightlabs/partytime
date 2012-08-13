var chart1; // globally available
$(document).ready(function() {
      chart1 = new Highcharts.Chart({
         chart: {
            renderTo: 'weekInParties',
            type: 'area'
         },
         title: {
            text: 'The Week In Parties'
         },
         xAxis: {
            categories: [{% for thisdate in dates%}'{{thisdate|date:"n/j"}}'{% if forloop.last %}{% else %},{% endif %}{% endfor %}]
         },
         yAxis: {
            title: {
               text: 'Number'
            }
         },
         series: [{
            name: 'Parties',
            data: [{% for data in data_dict %}{{ data }}{% if forloop.last %}{% else %},{% endif %}{% endfor %}]
         }]

      });
   });