var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.DkuUrlLinkCellRenderer = function (props) {
    return React.createElement(
        'a',
        {href: props.value, target: '_blank', rel: 'noopener noreferrer'},
        props.value
    );
};