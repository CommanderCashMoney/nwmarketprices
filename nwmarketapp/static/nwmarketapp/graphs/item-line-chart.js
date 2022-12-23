let lineChart = null;

function create_linegraph(graphData) {
    console.log("creating linegraphg...")
    console.log(graphData)
    const dates = []
    const prices = []
    const num_listings = []
    const avg_prices = []
    const buy_orders = []

    for(let i=0; i < graphData.length; i++) {
        let dateObj = new Date(graphData[i]["price_date"]);
        prices.push([dateObj / 1, graphData[i]["lowest_price"]]);
        avg_prices.push([dateObj / 1, graphData[i]["rolling_average"]]);
        num_listings.push([dateObj / 1, graphData[i]["avail"]]);
        buy_orders.push([dateObj / 1, graphData[i]["highest_buy_order"]]);

    }

    //	  LINE CHART
    lineChart = Highcharts.chart('line-graph-container', {
    chart: {
        zoomType: 'x',
        height: 250
    },
    title: {
        text: null
    },
    xAxis: {
        type: 'datetime'
    },
    yAxis: [{
        title: {
            text: 'Price'
        }
    }, {
        title: {
            text: 'Num listings',

        },opposite: true,
        height: "100%",
        top: "0%",
        lineWidth: 0,
        gridLineWidth: 0,
        minorTickLength: 0,
        tickLength: 0,
    }],
    plotOptions: {
        area: {
            fillColor: {
                linearGradient: {
                    x1: 0,
                    y1: 0,
                    x2: 0,
                    y2: 1
                },
                stops: [
                    [0, Highcharts.getOptions().colors[0]],
                    [1, Highcharts.color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                ]
            },
            marker: {
                radius: 1
            },
            lineWidth: 1,
            states: {
                hover: {
                    lineWidth: 1
                }
            },
            threshold: null
        }
    },
    tooltip: {
        xDateFormat: '%A, %b %e, %H:%M',
        shared: true,
        split: false,
        enabled: true
    },
    series: [
        {
            type: 'line',
            name: 'Price',
            data: prices,
            yAxis: 0,
            lineWidth: 3,
            color: 'rgb(55,115,204)',
            marker: {
                radius: 3,
                fillColor: "white",
                symbol: "circle"
            }
        },
        {
            type: 'line',
            name: 'Buy Order',
            data: buy_orders,
            yAxis: 0,
            lineWidth: 3,
            color: 'rgb(76,147,46)',
            marker: {
                radius: 2,
                fillColor: "green",
                symbol: "square"
            }
        },
        {
            type: 'spline',
            name: 'Cumulative Moving Average',
            data: avg_prices,
            yAxis: 0,
            lineWidth: 3,
            opacity: 0.70,
            color: 'rgb(55,115,204)',
            dashStyle: 'ShortDash',

            marker: {
                radius: 3,
                fillColor: "white",
                symbol: "circle"
            }
        },
        {
            type: 'column',
            name: 'Available',
            data: num_listings,
            yAxis: 1,
            color: 'rgb(49, 49, 55)',
            // pointWidth: 15,
            // groupPadding: 0,
            zIndex: -1,
            opacity: 0.85,
            borderWidth: 1,
            borderColor: '#ACACAC'
        },

        ]
    });

}

window.addEventListener("load",function(event) {
    Highcharts.createElement('link', {
        href: 'https://fonts.googleapis.com/css?family=Unica+One',
        rel: 'stylesheet',
        type: 'text/css'
    }, null, document.getElementsByTagName('head')[0]);

    Highcharts.theme = {
        colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066',
            '#eeaaee', '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'
        ],
        time: {
            useUTC: false
        },
        chart: {
            backgroundColor: '#3A3F47',
        },
        xAxis: {
            gridLineColor: '#707073',
            labels: {
                style: {
                    color: '#E0E0E3'
                }
            },
            lineColor: '#707073',
            tickColor: '#707073',
            title: {
                style: {
                    color: '#A0A0A3'

                }
            }
        },
        yAxis: {
            gridLineColor: '#707073',
            labels: {
                style: {
                    color: '#E0E0E3'
                }
            },
            lineColor: '#707073',
            minorGridLineColor: '#505053',
            tickColor: '#707073',
            tickWidth: 1,
            title: {
                style: {
                    color: '#A0A0A3'
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            style: {
                color: '#F0F0F0'
            }
        },
        plotOptions: {
            series: {
                dataLabels: {
                    color: '#F0F0F3',
                    style: {
                        fontSize: '13px'
                    }
                },
                marker: {
                    lineColor: '#333'
                }
            },
            boxplot: {
                fillColor: '#505053'
            },
            candlestick: {
                lineColor: 'white'
            },
            errorbar: {
                color: 'white'
            }
        },
        legend: {
            backgroundColor: '#3A3F47',
            itemStyle: {
                color: '#E0E0E3'
            },
            itemHoverStyle: {
                color: '#FFF'
            },
            itemHiddenStyle: {
                color: '#606063'
            },
            title: {
                style: {
                    color: '#C0C0C0'
                }
            }
        },
        credits: {
            style: {
                color: '#666'
            }
        },
        labels: {
            style: {
                color: '#707073'
            }
        },

        drilldown: {
            activeAxisLabelStyle: {
                color: '#F0F0F3'
            },
            activeDataLabelStyle: {
                color: '#F0F0F3'
            }
        },

        navigation: {
            buttonOptions: {
                symbolStroke: '#DDDDDD',
                theme: {
                    fill: '#505053'
                }
            }
        },

        // scroll charts
        rangeSelector: {
            buttonTheme: {
                fill: '#505053',
                stroke: '#000000',
                style: {
                    color: '#CCC'
                },
                states: {
                    hover: {
                        fill: '#707073',
                        stroke: '#000000',
                        style: {
                            color: 'white'
                        }
                    },
                    select: {
                        fill: '#000003',
                        stroke: '#000000',
                        style: {
                            color: 'white'
                        }
                    }
                }
            },
            inputBoxBorderColor: '#505053',
            inputStyle: {
                backgroundColor: '#333',
                color: 'silver'
            },
            labelStyle: {
                color: 'silver'
            }
        },

        navigator: {
            handles: {
                backgroundColor: '#666',
                borderColor: '#AAA'
            },
            outlineColor: '#CCC',
            maskFill: 'rgba(255,255,255,0.1)',
            series: {
                color: '#7798BF',
                lineColor: '#A6C7ED'
            },
            xAxis: {
                gridLineColor: '#505053'
            }
        },

        scrollbar: {
            barBackgroundColor: '#808083',
            barBorderColor: '#808083',
            buttonArrowColor: '#CCC',
            buttonBackgroundColor: '#606063',
            buttonBorderColor: '#606063',
            rifleColor: '#FFF',
            trackBackgroundColor: '#404043',
            trackBorderColor: '#404043'
        }
    };

// Apply the theme
    Highcharts.setOptions(Highcharts.theme);
});
function create_mini_graph(graphData, div_id) {

    const dates = []
    const prices = []
    const avg_prices = []
    // const buy_orders = []

    for(let i=0; i < graphData.length; i++) {
        let dateObj = new Date(graphData[i]["price_date"]);
        prices.push([dateObj / 1, graphData[i]["lowest_price"]]);
        avg_prices.push([dateObj / 1, graphData[i]["rolling_average"]]);
        // num_listings.push([dateObj / 1, graphData[i]["avail"]]);
        // buy_orders.push([dateObj / 1, graphData[i]["highest_buy_order"]]);

    }
    miniChart = Highcharts.chart(div_id, {
        chart: {
            type: 'line',
            backgroundColor:'#3A3F47',
            plotBorderWidth: 0,
            marginTop: 0,
            marginBottom: 0,
            marginLeft:10,
            plotShadow: false,
            borderWidth: 0,
            plotBorderWidth: 0,
            marginRight:10
        },
         tooltip: {
             xDateFormat: '%A, %b %e, %H:%M',
            shared: true,
            split: false,
             outside: true,
             hideDelay: 100,
            // enabled: true,
             userHTML: true,
             style: {
                 padding: 0,
                 width: 0,
                 height: 0,
             }

         },
        title: {
            text: ''
        },
        xAxis: {
        type: 'datetime',
            enabled:false,
            showEmpty:false,
        },
        // xAxis: {
        //     enabled:false,
        //     showEmpty:false,
        // },
        yAxis: {
            min: 0,
            title: {
                text: ''
            },
            showEmpty:false,
            enabled:false
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled:false
        },
        plotOptions: {
            line:{
                lineWidth:1.5,
            },
             showInLegend: false,
             tooltip: {}
        },
        series: [
            {
            marker: {
                enabled: false
                },
            // animation:false,
            name: '',
            data: prices
            },

        {
            name: '',
            data: avg_prices,
            opacity: 0.3,
            dashStyle: 'ShortDash',
            marker: {
                 enabled: false
            }
        },
        ]
    });



};

