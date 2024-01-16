'use strict';

$(function () {
  function footerPosition() {
    $("index-footer").removeClass("fixed-bottom");
    var contentHeight = document.body.scrollHeight,//网页正文全文高度
      winHeight = window.innerHeight;//可视窗口高度，不包括浏览器顶部工具栏
    if (contentHeight < winHeight) {
      //当网页正文高度小于可视窗口高度时，为footer添加类fixed-bottom
      $("footer").addClass("fixed-bottom");
    }
  }
  footerPosition();
  $(window).resize(footerPosition);
});


document.addEventListener('DOMContentLoaded', function () {

  // Toggles
  var $burgers = getAll('.burger');
  if ($burgers.length > 0) {
    $burgers.forEach(function ($el) {
      $el.addEventListener('click', function () {
        var target = $el.dataset.target;
        var $target = document.getElementById(target);
        $el.classList.toggle('is-active');
        $target.classList.toggle('is-active');
      });
    });
  }

  // Modals
  var $html = document.documentElement;
  var $modals = getAll('.modal');
  var $modalButtons = getAll('.modal-button');
  var $modalCloses = getAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button');

  if ($modalButtons.length > 0) {
    $modalButtons.forEach(function ($el) {
      $el.addEventListener('click', function () {
        var target = $el.dataset.target;
        var $target = document.getElementById(target);
        $html.classList.add('is-clipped');
        $target.classList.add('is-active');
      });
    });
  }

  if ($modalCloses.length > 0) {
    $modalCloses.forEach(function ($el) {
      $el.addEventListener('click', function () {
        $html.classList.remove('is-clipped');
        closeModals();
      });
    });
  }

  document.addEventListener('keydown', function (e) {
    if (e.keyCode === 27) {
      $html.classList.remove('is-clipped');
      closeModals();
    }
  });

  function closeModals() {
    $modals.forEach(function ($el) {
      $el.classList.remove('is-active');
    });
  }

  // Clipboard

  var $highlights = getAll('.highlight');
  var itemsProcessed = 0;

  if ($highlights.length > 0) {
    $highlights.forEach(function ($el) {
      var copy = '<button class="copy">Copy</button>';
      var expand = '<button class="expand">Expand</button>';
      $el.insertAdjacentHTML('beforeend', copy);

      if ($el.firstElementChild.scrollHeight > 480 && $el.firstElementChild.clientHeight <= 480) {
        $el.insertAdjacentHTML('beforeend', expand);
      }

      itemsProcessed++;
      if (itemsProcessed === $highlights.length) {
        addHighlightControls();
      }
    });
  }

  function addHighlightControls() {
    var $highlightButtons = getAll('.highlight .copy, .highlight .expand');

    $highlightButtons.forEach(function ($el) {
      $el.addEventListener('mouseenter', function () {
        $el.parentNode.style.boxShadow = '0 0 0 1px #ed6c63';
      });

      $el.addEventListener('mouseleave', function () {
        $el.parentNode.style.boxShadow = 'none';
      });
    });

    var $highlightExpands = getAll('.highlight .expand');

    $highlightExpands.forEach(function ($el) {
      $el.addEventListener('click', function () {
        $el.parentNode.firstElementChild.style.maxHeight = 'none';
      });
    });
  }
  // Functions

  function getAll(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector), 0);
  }
});


// FROM https://flatuicolors.com/palette/cn  and remove white
const ColorScheme = [
  "rgb(236, 204, 104)", "rgb(255, 127, 80)", "rgb(255, 107, 129)", "rgb(164, 176, 190)",
  "rgb(255, 165, 2)", "rgb(255, 99, 72)", "rgb(255, 71, 87)", "rgb(116, 125, 140)",
  "rgb(123, 237, 159)", "rgb(112, 161, 255)", "rgb(83, 82, 237)", "rgb(223, 228, 234)",
  "rgb(46, 213, 115)", "rgb(30, 144, 255)", "rgb(55, 66, 250)", "rgb(206, 214, 224)",
]


var getRandomColor = function () {
  return ColorScheme[Math.floor(Math.random() * ColorScheme.length)]
}

var getRandomColorSets = function (num) {
  var colorData = []
  for (var i = 0; i < num; i++) {
    colorData.push(getRandomColor())
  }
  return colorData
}

var genLineChart = function (id, config_data) {
  let chartStatus = Chart.getChart(id);
  if (chartStatus != undefined) {
    chartStatus.destroy();
  }
  var ctx = document.getElementById(id);
  var myChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: config_data.labels,
      datasets: [
        {
          label: config_data.title,
          data: config_data.data,
          backgroundColor: getRandomColor(),
          borderColor: getRandomColor,
          borderWidth: 1,
        },
      ],
    },
    options: {
      hover: {
        mode: "nearest",
        intersect: true,
      },
      title: {
        display: true,
        text: config_data.title,
      },
      elements: {
        point: {
          radius: 2,
        },
      },
      responsive: true,
      maintainAspectRatio: false,
      legend: {
        display: true,
      },
      scales: {
        xAxes: [
          {
            display: true,
            scaleLabel: {
              display: true,
              labelString: config_data.x_label,
            },
          },
        ],
        yAxes: [
          {
            display: true,
            ticks: { beginAtZero: true },
            scaleLabel: {
              display: true,
              labelString: config_data.y_label,
            },
          },
        ],
      },
    },
  });
  return myChart;
};

var genBarChart = function (id, config_data) {
  let chartStatus = Chart.getChart(id);
  if (chartStatus != undefined) {
    chartStatus.destroy();
  }
  var ctx = document.getElementById(id);
  var myChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: config_data.labels,
      datasets: [
        {
          label: config_data.title,
          data: config_data.data,
          backgroundColor: getRandomColor(),
          borderColor: getRandomColor,
          borderWidth: 1,
        },
      ],
    },
    options: {
      hover: {
        mode: "nearest",
        intersect: true,
      },
      title: {
        display: true,
        text: config_data.title,
      },
      elements: {
        point: {
          radius: 2,
        },
      },
      responsive: true,
      maintainAspectRatio: false,
      legend: {
        display: true,
      },
      scales: {
        xAxes: [
          {
            display: true,
            scaleLabel: {
              display: true,
              labelString: config_data.x_label,
            },
          },
        ],
        yAxes: [
          {
            display: true,
            ticks: { beginAtZero: true },
            scaleLabel: {
              display: true,
              labelString: config_data.y_label,
            },
          },
        ],
      },
    },
  });
  return myChart;
};
