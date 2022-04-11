const drawBar = () => {
    Highcharts.chart('competitive-bar-container', {
        chart: {
            type: 'bar',
            height: "300px"
        },
        title: {
            text: null
        },
        xAxis: {
            categories: ['Reinforced Orichalcum Great Axe Charm', "Iron Guardsman's Insignia", "Another Item", "Some super long text to test what happens when its long", "Another","Another","Another","Another","Another","Another",],
        },
        yAxis: {
            min: 0,
            title: {
                text: null,
                align: 'high',
            },
            labels: {
                overflow: 'justify',
            },
        },
        plotOptions: {
            bar: {
                 groupPadding: 0,
                 pointPadding: 0.2,
                 borderWidth: 0,
            },
        },
        legend: {
            enabled: false
        },
        series: [{
            name: 'Number of Different Prices',
            data: [
                {color: 'pink', y: 80},
                {color: 'orange', y: 65},
                {color: 'yellow', y: 55},
                {color: 'lightblue', y: 50},
                {color: 'blue', y: 45},
                {color: 'purple', y: 40},
                {color: 'darkgreen', y: 35},
                {color: 'violet', y: 30},
                {color: 'brown', y: 25},
                {color: 'red', y: 20},
            ]
        }]
    });
}

window.onload = () => {
        Highcharts.createElement('link', {
        href: 'https://fonts.googleapis.com/css?family=Unica+One',
        rel: 'stylesheet',
        type: 'text/css'
    }, null, document.getElementsByTagName('head')[0]);

    Highcharts.theme = {
        chart: {
            backgroundColor: 'rgb(40, 47, 47)',
            plotBorderColor: null,
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            style: {
                color: '#F0F0F0'
            }
        },
    };
    Highcharts.setOptions(Highcharts.theme);
    drawBar();
}