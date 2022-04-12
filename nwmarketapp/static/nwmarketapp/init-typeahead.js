const initTypeahead = (data) => {
    $.typeahead({
        input: '.item-search',
        order: "asc",
        display: "name",
        source: {data: data},
        callback: {
            onInit: function (node) {
                console.log('Typeahead Initiated on ' + node.selector);
            },
            onClickAfter: function(node, a, item, event){
                loadItem(item.id);
            },
            onSubmit: function (node, form, item, event) {
                loadItem(item.id);
            }
        }
    })
}