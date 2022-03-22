document.addEventListener("DOMContentLoaded", () => {
    fetch("/typeahead/").then(
        (response) => response.json()
    ).then(
        (data) => initTypeahead(data)
    ).catch((err) => {
        console.log(err);
    })
});

const initTypeahead = (data) => {
    $.typeahead({
        input: '.js-typeahead-names',
        order: "asc",
        display: "name",
        source: {
            url: "/cn",
            data: data
        },
        callback: {
            onInit: function (node) {
                console.log('Typeahead Initiated on ' + node.selector);
            },
            onClickAfter: function(node, a, item, event){
                const cn = item.id;
                $.ajax({
                    type: 'GET',
                    url: "",
                    success: function (response) {
                        update_prices(response);
                        createLinegraph(response)
                        let name = $(".js-typeahead-names").eq(0).val();
                        let win_title = 'New World Market Prices' + cn_id
                        let new_url = `/${cn}/${server_id}`;
                        window.history.pushState('data', win_title, new_url);
                        gtag('event', 'search-input', {'term': name});
                        $.getScript("https://www.googletagmanager.com/gtag/js?id=G-WW3EJQVND0",function(){});
                    },

                    error: function (response) {
                        console.log(response)
                    }
                })

            },
            onSubmit: function (node, form, item, event) {
                event.preventDefault();
                const cn_id = item.id
                const form_data = {cn_id}

                $.ajax({
                    type: 'GET',
                    url: "",
                    data: form_data,
                    success: function (response) {
                        update_prices(response);
                        createLinegraph(response)
                        let name = $(".js-typeahead-names").eq(0).val();

                        gtag('event', 'search-input', {'term': name});
                        $.getScript("https://www.googletagmanager.com/gtag/js?id=G-WW3EJQVND0",function(){});
                    },

                    error: function (response) {
                        console.log(response)
                    }
                })
            }

        }
    })
}