# AUTO GENERATED FILE - DO NOT EDIT

#' @export
dashTabulator <- function(id=NULL, applyBulkEdit=NULL, cellEdited=NULL, columns=NULL, data=NULL, groupBy=NULL, multiRowsClicked=NULL, options=NULL) {
    
    props <- list(id=id, applyBulkEdit=applyBulkEdit, cellEdited=cellEdited, columns=columns, data=data, groupBy=groupBy, multiRowsClicked=multiRowsClicked, options=options)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'DashTabulator',
        namespace = 'dash_tabulator',
        propNames = c('id', 'applyBulkEdit', 'cellEdited', 'columns', 'data', 'groupBy', 'multiRowsClicked', 'options'),
        package = 'dashTabulator'
        )

    structure(component, class = c('dash_component', 'list'))
}
