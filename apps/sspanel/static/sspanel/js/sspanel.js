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




'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // Toggles

  var $burgers = getAll('.burger');
  var $fries = getAll('.fries');

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




function genRandomRgbaSet(num) {
  colorData = []
  for (var i = 0; i < num; i++) {
    var r = Math.floor(Math.random() * 256);          // Random between 0-255
    var g = Math.floor(Math.random() * 256);          // Random between 0-255
    var b = Math.floor(Math.random() * 256);          // Random between 0-255
    var rgba = 'rgba(' + r + ',' + g + ',' + b + ',' + 0.2 + ')'; // Collect all to a string
    colorData.push(rgba)
  }
  return colorData

}



var getRandomColor = function () {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

var getRandomColorSets = function (num) {
  colorData = []
  for (var i = 0; i < num; i++) {
    colorData.push(getRandomColor())
  }
  return colorData
}

var genDoughnutChart = function (chartId, title, labels, data) {
  var ctx = $('#' + chartId)
  var myChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: getRandomColorSets(data.length),
      }]
    },
    options: {
      title: {
        display: true,
        positon: 'top',
        text: title,
      },
      legend: {
        display: true,
        position: 'bottom',
      },
      tooltip: {
        enabled: false,
      },
      scaleOverlay: true,
    }
  });
}

var genLineChart = function (chartId, config) {
  /**
      charId : 元素id 定位canvas用
      config : 配置信息 dict类型
          congig = {
              title: 图表名字
              labels :data对应的label
              data_title: data的标题
              data: 数据
              x_label : x轴的lable
              y_label : y轴的lable
          }
  **/
  var ctx = $('#' + chartId)
  var myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: config.labels,
      datasets: [{
        label: config.data_title,
        data: config.data,
        backgroundColor: getRandomColor(),
        borderColor: getRandomColor(),
        steppedLine: false,
        fill: false,
      }]
    },
    options: {
      responsive: true,
      title: {
        display: true,
        text: config.title,
      },
      hover: {
        mode: 'nearest',
        intersect: true
      },
      scales: {
        xAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: config.x_label,
          }
        }],
        yAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: config.y_label,
          }
        }]
      }
    }
  })
}
var genBarChart = function (chartId, config) {
  /**
      charId : 元素id 定位canvas用
      config : 配置信息 dict类型
          {
              title: 图表名字
              labels :data对应的label
              data_title: data的标题
              data: 数据
          }
  **/
  var ctx = $('#' + chartId)
  var myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: config.labels,
      datasets: [{
        label: config.data_title,
        data: config.data,
        backgroundColor: genRandomRgbaSet(config.data.length),
      }]
    },
    options: {
      scales: {
        yAxes: [{
          ticks: {
            beginAtZero: true,
            stepSize: 1,
            suggestedMax: 7
          }
        }]
      }
    }
  })
}

