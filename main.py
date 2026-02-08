"""
Bokeh server application for visualizing reflectance data of black and white materials.

Displays total reflectance, specular reflectance, and lambertian reflectance
measurements in interactive plots with filtering, range adjustment, and data download.

Launch with: bokeh serve --show reflectance-plots
"""
from os.path import dirname, join

from bokeh.palettes import Turbo256, Category10_10
from bokeh.models import (
    ColumnDataSource, Select, MultiChoice, Div, TabPanel, Tabs,
    Button, CustomJS, CheckboxGroup, RangeSlider,
)
from bokeh.layouts import row, column
from bokeh.io import curdoc

import pandas as pd
import plot_tools

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
DATA_DIR = join(dirname(__file__), "data")

black_spec_mat = pd.read_csv(
    join(DATA_DIR, "Specular_Reflect_Data", "Specular_material.csv")
).set_index("Angle (Deg)")

INITIAL_INTENSITY = 10.4629235
black_spec_mat = black_spec_mat / INITIAL_INTENSITY

black_spec_ref_ds = ColumnDataSource(black_spec_mat)
black_spec_ratio_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Specular_Reflect_Data", "Spec_Ratio.csv")).set_index("Angle (Deg)")
)

black_tot_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Total_Reflect_Data", "Black_Materials_total_reflecatance.csv")).set_index("nm")
)
white_tot_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Total_Reflect_Data", "SPIE18_white_all.csv")).set_index("nm")
)

white_lamb_pow_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Reflect_Power.csv")).set_index("Angle (Deg)")
)
white_lamb_scaled_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Reflect_Scaled.csv")).set_index("Angle (Deg)")
)
white_lamb_res_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Resid.csv")).set_index("Angle (Deg)")
)

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
total_fig = plot_tools.make_plot("Wavelength (nm)", "Total Reflectance (%)", "Total Reflectance vs Wavelength")
total_fig.x_range.start = 250
total_fig.x_range.end = 2500

spec_fig = plot_tools.make_plot("Angle (degrees)", "Specular Reflectance", "Specular Reflectance vs Angle")
lamb_fig = plot_tools.make_plot("Angle (degrees)", "Power (uW)", "Lambertian Reflectance vs Angle")
lamb_resid_fig = plot_tools.make_plot("Angle (degrees)", "Residual", "Lambertian Residual vs Angle")

total_fig.name = "total"
spec_fig.name = "spec"
lamb_fig.name = "lamb"
lamb_resid_fig.name = "resid"

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------
n_black_cols = len([c for c in black_tot_ds.data if c != "nm"])
n_white_cols = len([c for c in white_tot_ds.data if c != "nm"])
n_total = n_black_cols + n_white_cols

# Sample evenly from Turbo256 for total reflectance (many materials)
total_palette = [Turbo256[int(i * 255 / max(n_total - 1, 1))] for i in range(n_total)]
black_palette = total_palette[:n_black_cols]
white_palette = total_palette[n_black_cols:]

# Category10 for specular/lambertian (fewer materials)
spec_palette = Category10_10
lamb_palette = Category10_10

# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------
black_tot_renderers = plot_tools.plot_lines(
    black_tot_ds, total_fig, "nm", black_palette, False, ["black_tot"]
)
white_tot_renderers = plot_tools.plot_lines(
    white_tot_ds, total_fig, "nm", white_palette, False, ["white_tot"]
)

black_spec_ref_renderers = plot_tools.plot_lines(
    black_spec_ref_ds, spec_fig, "Angle (Deg)", spec_palette, False, ["black_spec"]
)
black_spec_ratio_renderers = plot_tools.plot_lines(
    black_spec_ratio_ds, spec_fig, "Angle (Deg)", spec_palette, False, ["black_ref"]
)

white_lamb_renderers = plot_tools.plot_lines(
    white_lamb_scaled_ds, lamb_fig, "Angle (Deg)", lamb_palette, False, ["white_lamb"]
)
white_lamb_pow_renderers = plot_tools.plot_lines(
    white_lamb_pow_ds, lamb_fig, "Angle (Deg)", lamb_palette, False, ["white_lamb"],
    line_dash="dotdash",
)
white_lamb_resid_renderers = plot_tools.plot_lines(
    white_lamb_res_ds, lamb_resid_fig, "Angle (Deg)", lamb_palette, False, ["white_res"],
    line_dash="dotdash",
)

all_black_renderers = black_tot_renderers + black_spec_ref_renderers
all_white_renderers = (
    white_tot_renderers + white_lamb_renderers
    + white_lamb_pow_renderers + white_lamb_resid_renderers
)
all_renderers = (
    black_tot_renderers + white_tot_renderers
    + black_spec_ref_renderers + black_spec_ratio_renderers
    + white_lamb_renderers + white_lamb_pow_renderers
    + white_lamb_resid_renderers
)

# ---------------------------------------------------------------------------
# Material multi-choice list (deduplicated, preserving order)
# ---------------------------------------------------------------------------
seen = set()
multi_choice_options = []
for rnd in all_renderers:
    if rnd.name not in seen:
        seen.add(rnd.name)
        multi_choice_options.append(rnd.name)

# ---------------------------------------------------------------------------
# Checkbox groups for selective download
# ---------------------------------------------------------------------------
checkbox_groups = []

btk_text = Div(text="<b>Black Total Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_tot_ds.column_names[1:], width=215))

wtk_text = Div(text="<b>White Total Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_tot_ds.column_names[1:]))

bsk_text = Div(text="<b>Black Specular Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_spec_ref_ds.column_names[1:], width=125))

bsrk_text = Div(text="<b>Black Specular Ratio:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_spec_ratio_ds.column_names[1:], width=125))

wls_text = Div(text="<b>White Lambertian Scaled:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_scaled_ds.column_names[1:], width=125))

wlss_text = Div(text="<b>White Lambertian Power:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_pow_ds.column_names[1:], width=125))

wrs_text = Div(text="<b>White Lambertian Residual:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_res_ds.column_names[1:], width=125))

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
multi_choice = MultiChoice(
    title="Show/Hide Materials",
    options=multi_choice_options,
    name="multi",
    placeholder="Type or select materials...",
)

mat_color_select = Select(
    title="Filter Material Color",
    options=["Select Material", "Black", "White", "All"],
    value="Select Material",
    name="color",
)

spec_select = Select(
    title="Specular Variable Type",
    options=["Reflectance", "Ratio"],
    name="spec_select",
)

# Built-in RangeSliders (replacing custom IonRangeSlider)
tot_slider = RangeSlider(
    start=250, end=2500, value=(250, 2500), step=1,
    title="Total Reflectance Wavelength Range (nm)",
)
spec_slider = RangeSlider(
    start=10, end=160, value=(10, 160), step=1,
    title="Specular Reflectance Angle Range",
)
lamb_slider = RangeSlider(
    start=10, end=90, value=(10, 90), step=1,
    title="Lambertian Reflectance Angle Range",
)
resid_slider = RangeSlider(
    start=10, end=90, value=(10, 90), step=1,
    title="Lambertian Residual Angle Range",
)

# Download buttons
totb_button = Button(label="Download Black Total Reflectance", button_type="success")
totw_button = Button(label="Download White Total Reflectance", button_type="success")
spec_button = Button(label="Download Specular Reflectance", button_type="success")
spec_rat_button = Button(label="Download Specular Ratio", button_type="success")
lamb_button = Button(label="Download Lambertian Reflectance", button_type="success")
resid_button = Button(label="Download Lambertian Residual", button_type="success")
selec_button = Button(label="Download Selected Materials", button_type="primary")

# "No Data" labels
tot_fig_label = plot_tools.make_label(total_fig, True)
spec_fig_label = plot_tools.make_label(spec_fig, True)
lamb_fig_label = plot_tools.make_label(lamb_fig, True)

# ---------------------------------------------------------------------------
# Hover tools
# ---------------------------------------------------------------------------
total_fig.add_tools(plot_tools.make_hovertool("nm", "Wavelength (nm)", "Total Reflectance %"))
spec_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Specular Reflectance"))
lamb_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Lambertian Reflectance"))
lamb_resid_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Residual"))

total_fig.add_layout(tot_fig_label)
spec_fig.add_layout(spec_fig_label)
lamb_fig.add_layout(lamb_fig_label)
lamb_resid_fig.add_layout(lamb_fig_label)

# ---------------------------------------------------------------------------
# Python callbacks
# ---------------------------------------------------------------------------
def check_for_data(renderers):
    """Return True if no renderer in the list is visible (i.e. show 'No Data')."""
    return not any(r.visible for r in renderers)


def update_mat_color(attr, old, new):
    if new == "Select Material":
        for r in all_renderers:
            r.visible = False
        tot_fig_label.visible = True
        spec_fig_label.visible = True
        lamb_fig_label.visible = True
        spec_select.disabled = True
    elif new == "All":
        for r in all_renderers:
            r.visible = True
        tot_fig_label.visible = False
        spec_fig_label.visible = False
        lamb_fig_label.visible = False
        spec_select.disabled = False
    else:
        is_white = new == "White"
        for r in all_black_renderers:
            r.visible = not is_white
        for r in all_white_renderers:
            r.visible = is_white
        spec_select.disabled = is_white
        spec_fig_label.visible = is_white
        tot_fig_label.visible = False
        lamb_fig_label.visible = not is_white


def update_spec(attr, old, new):
    is_ratio = new == "Ratio"
    spec_fig.yaxis.axis_label = "Specular Ratio (%)" if is_ratio else "Specular Reflectance"
    for r in black_spec_ratio_renderers:
        r.visible = is_ratio
    for r in black_spec_ref_renderers:
        r.visible = not is_ratio


def update_tot_slider(attr, old, new):
    total_fig.x_range.start, total_fig.x_range.end = new


def update_spec_slider(attr, old, new):
    spec_fig.x_range.start, spec_fig.x_range.end = new


def update_lamb_slider(attr, old, new):
    lamb_fig.x_range.start, lamb_fig.x_range.end = new


def update_resid_slider(attr, old, new):
    lamb_resid_fig.x_range.start, lamb_resid_fig.x_range.end = new


def update_multi_choice(attr, old, new):
    selected = set(multi_choice.value)
    for r in all_renderers:
        r.visible = r.name in selected
    tot_fig_label.visible = check_for_data(black_tot_renderers + white_tot_renderers)
    spec_fig_label.visible = check_for_data(black_spec_ref_renderers)
    lamb_fig_label.visible = check_for_data(white_lamb_renderers)


# Wire up callbacks
mat_color_select.on_change("value", update_mat_color)
spec_select.on_change("value", update_spec)
multi_choice.on_change("value", update_multi_choice)
tot_slider.on_change("value", update_tot_slider)
spec_slider.on_change("value", update_spec_slider)
lamb_slider.on_change("value", update_lamb_slider)
resid_slider.on_change("value", update_resid_slider)

# ---------------------------------------------------------------------------
# JavaScript download callbacks
# ---------------------------------------------------------------------------
download_js = open(join(dirname(__file__), "download.js")).read()
selec_js = open(join(dirname(__file__), "selec_download.js")).read()

totb_button.js_on_click(CustomJS(args=dict(source=black_tot_ds), code=download_js))
totw_button.js_on_click(CustomJS(args=dict(source=white_tot_ds), code=download_js))
spec_button.js_on_click(CustomJS(args=dict(source=black_spec_ref_ds), code=download_js))
spec_rat_button.js_on_click(CustomJS(args=dict(source=black_spec_ratio_ds), code=download_js))
lamb_button.js_on_click(CustomJS(args=dict(source=white_lamb_scaled_ds), code=download_js))
resid_button.js_on_click(CustomJS(args=dict(source=white_lamb_res_ds), code=download_js))
selec_button.js_on_click(
    CustomJS(args=dict(groups=checkbox_groups, rnds=all_renderers), code=selec_js)
)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
instructions = Div(text="""
<h3 style="margin-top:0">Welcome</h3>
<p>Interactive visualization of Black and White materials reflectance data.
Use the tabs above to filter materials, adjust axis ranges, or download data.</p>
""")

filter_help = Div(text="""
<details open>
  <summary><b>Filters</b></summary>
  <p>Use <em>Filter Material Color</em> to show black, white, or all materials.
  Use <em>Show/Hide Materials</em> to select individual materials by name.</p>
</details>
<details>
  <summary><b>Range Sliders</b></summary>
  <p>Adjust the wavelength or angle range displayed on each plot.</p>
</details>
<details>
  <summary><b>Downloads</b></summary>
  <p>Select specific materials in the <em>Select Data</em> tab, then use the
  <em>Downloads</em> tab to export CSV files. You can also download full datasets.</p>
</details>
<details>
  <summary><b>Plot Tools</b></summary>
  <p>Each plot has a toolbar with box zoom, pan, wheel zoom, reset, and save.
  Hover over lines to see material name and values.</p>
</details>
""")

instr_layout = column(
    instructions, filter_help,
    sizing_mode="stretch_width",
)
filter_layout = row(
    mat_color_select, spec_select, multi_choice,
    sizing_mode="stretch_width",
)
slider_layout = column(
    tot_slider, spec_slider, lamb_slider, resid_slider,
    sizing_mode="stretch_width",
)
download_select_layout = row(
    column(btk_text, checkbox_groups[0]),
    column(wtk_text, checkbox_groups[1]),
    column(bsk_text, checkbox_groups[2], bsrk_text, checkbox_groups[3]),
    column(wls_text, checkbox_groups[4], wlss_text, checkbox_groups[5]),
    column(wrs_text, checkbox_groups[6]),
    sizing_mode="stretch_width",
)
download_buttons_layout = row(
    column(totb_button, totw_button),
    column(spec_button, spec_rat_button),
    column(lamb_button, resid_button, selec_button),
)

tabs = Tabs(
    tabs=[
        TabPanel(child=instr_layout, title="Instructions"),
        TabPanel(child=filter_layout, title="Filters"),
        TabPanel(child=slider_layout, title="Range Sliders"),
        TabPanel(child=download_select_layout, title="Select Data"),
        TabPanel(child=download_buttons_layout, title="Downloads"),
    ],
    active=0,
    name="tabs",
)

# Figure heights
spec_fig.height = 300
lamb_fig.height = 350
lamb_resid_fig.height = 350
total_fig.height = 300

# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
curdoc().add_root(total_fig)
curdoc().add_root(spec_fig)
curdoc().add_root(lamb_fig)
curdoc().add_root(lamb_resid_fig)
curdoc().add_root(tabs)
curdoc().title = "B/W Materials Reflectance Data"
