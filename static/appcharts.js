// Builds a 'doughnut'chart using Chart.js on expenses 'type' and 'category'
// Define the 'category' chart data
var categoryChartData = {
  labels: [{% for i in exp_cat %}"{{ i.category }}",{% endfor %}],
  datasets: [{
    data: [{% for i in exp_cat %}{{ i.partial }},{% endfor %}],
  }]
};

// Define the 'type' chart data
var typeChartData = {
  labels: [{% for i in exp_type %}"{{ i.type }}",{% endfor %}],
  datasets: [{
    data: [{% for i in exp_type %}{{ i.partial }},{% endfor %}],
  }]
};

// Doughnut chart options (apply to both charts)
var chartOptions = {
  legend: {
    position: 'bottom'
  },
  plugins: {
    colorschemes: {
      scheme: 'brewer.SetThree12'
    }
  }
};

// Get both charts canvas
var ctx1 = document.getElementById('categoryChart');
var ctx2 = document.getElementById('typeChart');

// Create the 'expenses category' chart using its chart canvas
var categoryChart = new Chart(ctx1, {
  type: 'doughnut',
  data: categoryChartData,
  options: chartOptions
});

// Create the 'expenses type' chart using its chart canvas
var typeChart = new Chart(ctx2, {
  type: 'doughnut',
  data: typeChartData,
  options: chartOptions
});

/* Returns a chart.js 'line' chart on a bootstrap modal when clicking on a
         renderered chart.js 'doughnut' chart item.*/
// Extract 'category label' when clicking on the 'doughnut' chart item
ctx1.onclick = function(evt) {
  var category = categoryChart.getElementAtEvent(evt)[0];
  if (category) {
    var label = categoryChart.data.labels[category._index];
  }

  /* jquery a sqlite3 database with this 'label' and get it's labels and
            data to populate a new chart*/
  $.get('/modal?category=' + label, function(lineChartData){
    var labels=[], data=[], i=0, j=0;
    for (i=0; i<lineChartData.length; i++){
      labels.push(lineChartData[i].month);
    }
    for (i=0; i<lineChartData.length; i++){
      data.push(lineChartData[i].partial);
    }

    // Create a modal chart with the colected labels and data
    var ctx3 = document.getElementById('lineChart');
    var lineChart = new Chart(ctx3, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          label: label,
          fill: false,
          pointStyle: 'line'
        }]
      },
      options: {
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true
            }
          }]
        },
        legend: {
          display: true,
          text: label,
          labels: {
            usePointStyle: true
          }
        },
      }
    });

    // show the created chart in a modal
    $('#myModal').modal('show');
    console.log(label, data, lineChartData);
  });
};


/* Returns a chart.js 'line' chart on a bootstrap modal when clicking on a
         renderered chart.js 'doughnut' chart item.*/
// Extract 'type label' when clicking on the 'doughnut' chart item
ctx2.onclick = function(evt) {
  var type = typeChart.getElementAtEvent(evt)[0];
  if (type) {
    var label = typeChart.data.labels[type._index];
  }

  /* jquery a sqlite3 database with this 'label' and get it's labels and
            data to populate a new chart*/
  $.get('/modal?type=' + label, function(lineChartData){
    var labels=[], data=[], i=0, j=0;
    for (i=0; i<lineChartData.length; i++){
      labels.push(lineChartData[i].month);
    }
    for (i=0; i<lineChartData.length; i++){
      data.push(lineChartData[i].amount);
    }

    // Create a modal chart with the colected labels and data
    var ctx3 = document.getElementById('lineChart');
    var lineChart = new Chart(ctx3, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          label: label,
          fill: false,
          pointStyle: 'line'
        }]
      },
      options: {
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true
            }
          }]
        },
        legend: {
          display: true,
          text: label,
          labels: {
            usePointStyle: true
          }
        },
      }
    });

    // Show the created chart in a modal
    $('#myModal').modal('show');
    console.log(label, data, lineChartData);
  });
};

