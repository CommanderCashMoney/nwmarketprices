function createLinegraph(response) {
    //	  LINE CHART
    const dates = []
    const prices = []
    var max_price = []
    $.each(response.price_graph_data, function () {
        let dateObj = new Date(this[0])
        let date = dateObj.getDate()
        let month = dateObj.getMonth() + 1
        let dt = month + '-' + date
        dates.push(dt)
        prices.push(this[1])

        max_price.push(this[1])

    });
    const avg_prices = []
    $.each(response.avg_graph_data, function () {
        avg_prices.push(this[1])
    });
    const num_listings = []
    $.each(response.num_listings, function () {
        num_listings.push(this)
    });


    var max_of_array = Math.max.apply(Math, max_price);


    {
        labels = ['1/08', '1/9', '1/10', '1/12', '1/13', '1/15', '1/17']
    }
    const line_data = {
        labels: dates,

        datasets: [{
            label: 'Lowest Price',
            yAxisID: 'y',
            data: prices,
            fill: false,
            borderColor: 'rgb(55, 115, 204)',
            backgroundColor: '#F3F3F3',
            tension: 0.1
        },
            {
                label: '15 Day Rolling Average',
                yAxisID: 'y',
                data: avg_prices,
                borderDash: [10, 5],
                fill: false,
                borderColor: 'rgb(55, 100, 155)',

                tension: 0.6
            },
            {
                type: 'bar',
                label: "Quantity",
                yAxisID: 'y2',
                data: num_listings,
                fill: false,
                tension: 0.1,
                backgroundColor: 'rgb(49,49,55)',


            },
        ]
    };
    var options1 = {
        scales: {
            x: {
                ticks: {
                    color: "#F3F3F3"
                },

            },
            y: {
                type: 'linear',
                position: 'left',
                ticks: {
                    color: "#F3F3F3"
                }
            },
            y2: {
                type: 'linear',
                position: 'right',
                ticks: {
                    max: 100,
                    min: 0
                },
                grid: {
                    display: false
                }
            }

        },
        color: "#F3F3F3",


    };
    if (window.chart != null) {
        window.chart.destroy();

    }

    var ctx = document.getElementById('linechart');
    window.chart = new Chart(ctx, {
        type: 'line',
        data: line_data,
        options: options1
    });
}
