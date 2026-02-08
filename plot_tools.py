"""Utility functions for creating and styling reflectance plots with Bokeh 3.x."""

from bokeh.plotting import figure
from bokeh.models import HoverTool, Label


def make_hovertool(x_field, x_label, y_label):
    """Create a hover tool that shows material name and data values."""
    hovertool = HoverTool(
        tooltips=[
            ("Material", "$name"),
            (x_label, f"@{x_field}{{0.1f}}"),
            (y_label, "@$name{0.4f}"),
        ],
        mode="mouse",
        line_policy="nearest",
    )
    return hovertool


def make_plot(x_label, y_label, title):
    """Create a styled figure with consistent formatting."""
    fig = figure(
        width=700,
        height=350,
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        title_location="above",
        sizing_mode="stretch_width",
        toolbar_location="below",
        tools="box_zoom,pan,wheel_zoom,reset,save",
        active_drag="box_zoom",
        output_backend="webgl",
    )
    fig.x_range.range_padding = 0
    fig.x_range.only_visible = True
    fig.y_range.only_visible = True

    # Title styling
    fig.title.text_font_size = "14px"
    fig.title.text_font_style = "bold"

    # Axis styling
    fig.xaxis.axis_label_text_font_size = "12px"
    fig.yaxis.axis_label_text_font_size = "12px"
    fig.xaxis.major_label_text_font_size = "10px"
    fig.yaxis.major_label_text_font_size = "10px"

    # Grid styling
    fig.xgrid.grid_line_alpha = 0.3
    fig.ygrid.grid_line_alpha = 0.3
    fig.xgrid.grid_line_dash = [4, 4]
    fig.ygrid.grid_line_dash = [4, 4]

    # Border
    fig.border_fill_alpha = 0
    fig.outline_line_color = "#cccccc"

    return fig


def plot_lines(ds, fig, index_col, palette, visible, tags, line_width=1.2, line_dash="solid"):
    """Generic line plotter for any data source."""
    renderers = []
    color_idx = 0
    for name in ds.data:
        if name != index_col:
            r = fig.line(
                index_col, name,
                line_width=line_width,
                line_dash=line_dash,
                color=palette[color_idx % len(palette)],
                source=ds,
                visible=visible,
                name=name,
                tags=tags,
                alpha=0.85,
            )
            renderers.append(r)
            color_idx += 1
    return renderers


def make_label(fig, visibility):
    """Create a centered 'No Data' label for a figure."""
    return Label(
        x=fig.width / 2,
        y=fig.height / 2,
        x_units="screen",
        y_units="screen",
        text="No Data For This Material",
        text_font_size="16px",
        text_color="#999999",
        text_font_style="italic",
        visible=visibility,
    )
