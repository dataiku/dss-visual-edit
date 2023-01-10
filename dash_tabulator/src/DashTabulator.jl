
module DashTabulator
using Dash

const resources_path = realpath(joinpath( @__DIR__, "..", "deps"))
const version = "0.0.1"

include("jl/dashtabulator.jl")

function __init__()
    DashBase.register_package(
        DashBase.ResourcePkg(
            "dash_tabulator",
            resources_path,
            version = version,
            [
                
            ]
        )

    )
end
end
