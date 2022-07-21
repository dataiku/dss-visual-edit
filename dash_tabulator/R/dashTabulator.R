# AUTO GENERATED FILE - DO NOT EDIT

#' @export
dashTabulator <- function(id=NULL, cellEdited=NULL, columns=NULL, data=NULL) {
    
    props <- list(id=id, cellEdited=cellEdited, columns=columns, data=data)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'DashTabulator',
        namespace = 'dash_tabulator',
        propNames = c('id', 'cellEdited', 'columns', 'data'),
        package = 'dashTabulator'
        )

    structure(component, class = c('dash_component', 'list'))
}
