let chart = null;

const drawBar = () => {
    let names = [];
    let colors = ["pink", "orange", "yellow", "lightblue", "blue", "purple", "darkgreen", "violet", "brown", "red"];
    let numData = [];
    for(let i=0; i<top10data.length; i++) {
        names.push(top10data[i][0]);
        numData.push({
            color: colors[i],
            y: top10data[i][1]
        });
    }
    chart = Highcharts.chart('competitive-bar-container', {
        chart: {
            type: 'bar',
            backgroundColor: '#454A51',
            plotBorderColor: null,
        },
        title: {
            text: null
        },
        xAxis: {
            categories: names,
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
            min: 0,
            title: {
                text: null,
                align: 'high',
            },
            gridLineColor: '#707073',
            labels: {
                overflow: 'justify',
                style: {
                    color: '#E0E0E3'
                }
            },
        },
        plotOptions: {
            bar: {
                 groupPadding: 0,
                 pointPadding: 0.2,
                 borderWidth: 0,
            },
        },
        credits: {
            style: {
                color: 'transparent'
            }
        },
        legend: {
            enabled: false
        },
        series: [{
            name: 'Number of Different Prices',
            data: numData
        }]
    });
    document.getElementById("competitive-items-ph").classList.add("hidden");
}

window.addEventListener('load', () => {
        Highcharts.createElement('link', {
        href: 'https://fonts.googleapis.com/css?family=Unica+One',
        rel: 'stylesheet',
        type: 'text/css'
    }, null, document.getElementsByTagName('head')[0]);
});

window.addEventListener('resize', function(event) {
    if(!chart) {
        return;
    }
    const cbc = document.getElementById("competitive-bar-column");
    const computedStyle = window.getComputedStyle(cbc);
    const fullWidth = Number(computedStyle.width.replace("px", ""));
    const pl = Number(computedStyle.paddingLeft.replace("px", ""));
    const pr = Number(computedStyle.paddingRight.replace("px", ""));
    chart.update({
        chart: {
            width: fullWidth - pl - pr
        }
    }, true, false, false);  // redraw=true, onetoone=false, animation=false
});
