let lineChart = null;

function create_linegraph(graphData, graphId) {

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
    lineChart = Highcharts.chart(graphId, {
     time: {
            useUTC: false
    },
    chart: {
        zoomType: 'x',
        height: 250,
        backgroundColor: 'transparent'
    },
    title: {
        text: null
    },
    xAxis: {
        type: 'datetime',
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
        yAxis: [{
            title: {
                text: 'Price',
                style: {
                    color: '#A0A0A3'
                }
            },
             gridLineColor: '#707073',
            labels: {
                style: {
                    color: '#E0E0E3'
                }
            },

        },
            {
                title: {
                    text: 'Num listings',
                     style: {
                        color: '#A0A0A3'
                     }

                },
                 gridLineColor: '#707073',


                opposite: true,
                height: "100%",
                top: "0%",
                lineWidth: 0,
                gridLineWidth: 0,
                minorTickLength: 0,
                tickLength: 0,
                tickWidth: 1,
                labels: {
                style: {
                    color: '#E0E0E3'
                }
            },
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
         legend: {
            backgroundColor: 'transparent',
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
                color: 'transparent'
            }
        },
    tooltip: {
        xDateFormat: '%A, %b %e, %H:%M',
        shared: true,
        split: false,
        enabled: true,
         backgroundColor: 'rgba(0, 0, 0, 0.85)',
            style: {
                color: '#F0F0F0'
            }
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


function create_mini_graph(graphData, div_id) {

    const dates = []
    const prices = []
    const avg_prices = []


    for(let i=0; i < graphData.length; i++) {
        let dateObj = new Date(graphData[i]["price_date"]);
        prices.push([dateObj / 1, graphData[i]["lowest_price"]]);
        avg_prices.push([dateObj / 1, graphData[i]["rolling_average"]]);


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
        time: {
            useUTC: false
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
                 color: '#F0F0F0'
             },
             backgroundColor: 'rgba(0, 0, 0, 0.85)',


         },
        title: {
            text: ''
        },
        xAxis: {
        type: 'datetime',
            enabled:false,
            showEmpty:false,

        },
   // '#2b908f', '#90ee7e'
        yAxis: {
            min: 0,
            title: {
                text: ''

            },
             gridLineColor: '#707073',
            labels: {
                style: {
                    color: '#E0E0E3'
                }
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
            name: 'Price',
            data: prices,
                color: 'rgb(55,115,204)',
            },

        {
            name: 'Avg',
            data: avg_prices,
            color: 'rgb(98,108,143)',
            opacity: 0.8,
            dashStyle: 'ShortDash',
            marker: {
                 enabled: false
            }
        },
        ]
    });



};

