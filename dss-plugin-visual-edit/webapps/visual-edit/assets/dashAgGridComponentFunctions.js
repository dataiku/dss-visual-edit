var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.VisualEditLinkComponent = function (props) {
    return React.createElement(
        'a',
        {href: props.value, target: '_blank', rel: 'noopener noreferrer'},
        props.value
    );
};

dagcomponentfuncs.CustomNoRowsOverlay = function (props) {
    return React.createElement(
        'div',
        {
            style: {
                border: '1pt solid grey',
                color: 'grey',
                padding: 10,
                fontSize: props.fontSize
            },
        },
        props.message
    );
};