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
    Highcharts.chart('competitive-bar-container', {
        chart: {
            type: 'bar',
            height: "300px"
        },
        title: {
            text: null
        },
        xAxis: {
            categories: names,
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
            data: numData
        }]
    });
    document.getElementById("competitive-items-ph").classList.add("hidden");
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
}