const initTypeahead = (data) => {
    $.typeahead({
        input: '.item-search',
        display: "name",
        source: {data: data},
        maxItem: 10,
        callback: {
            onInit: function (node) {
                console.log('Typeahead Initiated on ' + node.selector);
            },
            onClickAfter: function(node, a, item, event){
                loadItem(item.id);
            },
            onSubmit: function (node, form, item, event) {
                loadItem(item.id);
            },

        }
    })
}

$('.typeahead').bind('typeahead:render', function(ev, suggestion) {
  console.log('Selection: ' + suggestion);
});