"""Utility functions for creating and styling reflectance plots with Bokeh 3.x."""

from bokeh.plotting import figure
from bokeh.models import (
    HoverTool, CrosshairTool, Label, Band, ColumnDataSource,
    BoxAnnotation,
)


# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
PLOT_BG = "#1a1a2e"
PLOT_BORDER = "#16213e"
GRID_COLOR = "#2a2a4a"
TEXT_COLOR = "#e0e0e0"
TITLE_COLOR = "#ffffff"
AXIS_COLOR = "#888888"
CROSSHAIR_COLOR = "#ffffff"

# Spectral band colors (semi-transparent)
UV_COLOR = "#9b59b6"
VIS_COLOR = "#2ecc71"
NIR_COLOR = "#e74c3c"


def make_hovertool(x_field, x_label, y_label):
    """Create a styled hover tool with HTML tooltips."""
    hovertool = HoverTool(
        tooltips="""
        <div style="background:#1a1a2e; border:1px solid #3a3a5a; border-radius:6px;
                    padding:8px 12px; font-family:monospace; font-size:12px; color:#e0e0e0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
            <div style="font-weight:bold; color:#00d2ff; margin-bottom:4px;">$name</div>
            <div><span style="color:#888;">""" + x_label + """:</span> @""" + x_field + """{0.1f}</div>
            <div><span style="color:#888;">""" + y_label + """:</span> @$name{0.4f}</div>
        </div>
        """,
        mode="mouse",
        line_policy="nearest",
    )
    return hovertool


def make_crosshair():
    """Create a crosshair tool for precise readings."""
    return CrosshairTool(
        line_color=CROSSHAIR_COLOR,
        line_alpha=0.3,
        line_width=1,
    )


def make_plot(x_label, y_label, title):
    """Create a dark-themed styled figure with consistent formatting."""
    fig = figure(
        width=700,
        height=380,
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

    # Dark background
    fig.background_fill_color = PLOT_BG
    fig.border_fill_color = PLOT_BORDER
    fig.outline_line_color = "#2a2a4a"

    # Title styling
    fig.title.text_font_size = "15px"
    fig.title.text_font_style = "bold"
    fig.title.text_color = TITLE_COLOR

    # Axis styling
    fig.xaxis.axis_label_text_font_size = "12px"
    fig.yaxis.axis_label_text_font_size = "12px"
    fig.xaxis.major_label_text_font_size = "10px"
    fig.yaxis.major_label_text_font_size = "10px"
    fig.xaxis.axis_label_text_color = TEXT_COLOR
    fig.yaxis.axis_label_text_color = TEXT_COLOR
    fig.xaxis.major_label_text_color = AXIS_COLOR
    fig.yaxis.major_label_text_color = AXIS_COLOR
    fig.xaxis.axis_line_color = "#3a3a5a"
    fig.yaxis.axis_line_color = "#3a3a5a"
    fig.xaxis.major_tick_line_color = "#3a3a5a"
    fig.yaxis.major_tick_line_color = "#3a3a5a"
    fig.xaxis.minor_tick_line_color = None

    # Grid styling
    fig.xgrid.grid_line_color = GRID_COLOR
    fig.ygrid.grid_line_color = GRID_COLOR
    fig.xgrid.grid_line_alpha = 0.4
    fig.ygrid.grid_line_alpha = 0.4
    fig.xgrid.grid_line_dash = [2, 4]
    fig.ygrid.grid_line_dash = [2, 4]

    # Add crosshair
    fig.add_tools(make_crosshair())

    return fig


def add_spectral_bands(fig):
    """Add UV/VIS/NIR band annotations to a wavelength plot."""
    bands = [
        (250, 400, UV_COLOR, "UV", 0.06),
        (400, 700, VIS_COLOR, "Visible", 0.04),
        (700, 2500, NIR_COLOR, "NIR", 0.03),
    ]
    for left, right, color, _name, alpha in bands:
        fig.add_layout(BoxAnnotation(
            left=left, right=right,
            fill_alpha=alpha, fill_color=color,
            line_alpha=0,
        ))


def plot_lines(ds, fig, index_col, palette, visible, tags, line_width=1.5, line_dash="solid"):
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
                alpha=0.9,
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
        text="Select materials to display",
        text_font_size="16px",
        text_color="#555577",
        text_font_style="italic",
        visible=visibility,
    )
