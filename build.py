#!/usr/bin/env python3
"""
Build a standalone HTML page for GitHub Pages deployment.

All interactivity uses client-side CustomJS callbacks (no Python server needed).
Outputs to docs/index.html.

Usage: python build.py
"""
import os
from os.path import dirname, join

from bokeh.palettes import Turbo256, Category10_10
from bokeh.models import (
    ColumnDataSource, Select, MultiChoice, Div, TabPanel, Tabs,
    Button, CustomJS, CheckboxGroup, RangeSlider,
)
from bokeh.layouts import row, column, layout
from bokeh.resources import CDN
from bokeh.embed import file_html

import pandas as pd
import plot_tools

SCRIPT_DIR = dirname(os.path.abspath(__file__))
DATA_DIR = join(SCRIPT_DIR, "data")
OUT_DIR = join(SCRIPT_DIR, "docs")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
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
total_fig.height = 300

spec_fig = plot_tools.make_plot("Angle (degrees)", "Specular Reflectance", "Specular Reflectance vs Angle")
spec_fig.height = 300

lamb_fig = plot_tools.make_plot("Angle (degrees)", "Power (uW)", "Lambertian Reflectance vs Angle")
lamb_fig.height = 350

lamb_resid_fig = plot_tools.make_plot("Angle (degrees)", "Residual", "Lambertian Residual vs Angle")
lamb_resid_fig.height = 350

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------
n_black_cols = len([c for c in black_tot_ds.data if c != "nm"])
n_white_cols = len([c for c in white_tot_ds.data if c != "nm"])
n_total = n_black_cols + n_white_cols

total_palette = [Turbo256[int(i * 255 / max(n_total - 1, 1))] for i in range(n_total)]
black_palette = total_palette[:n_black_cols]
white_palette = total_palette[n_black_cols:]
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
# "No Data" labels & hover tools
# ---------------------------------------------------------------------------
tot_fig_label = plot_tools.make_label(total_fig, True)
spec_fig_label = plot_tools.make_label(spec_fig, True)
lamb_fig_label = plot_tools.make_label(lamb_fig, True)

total_fig.add_layout(tot_fig_label)
spec_fig.add_layout(spec_fig_label)
lamb_fig.add_layout(lamb_fig_label)
lamb_resid_fig.add_layout(lamb_fig_label)

total_fig.add_tools(plot_tools.make_hovertool("nm", "Wavelength (nm)", "Total Reflectance %"))
spec_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Specular Reflectance"))
lamb_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Lambertian Reflectance"))
lamb_resid_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Residual"))

# ---------------------------------------------------------------------------
# Multi-choice options (deduplicated)
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
    placeholder="Type or select materials...",
)

mat_color_select = Select(
    title="Filter Material Color",
    options=["Select Material", "Black", "White", "All"],
    value="Select Material",
)

spec_select = Select(
    title="Specular Variable Type",
    options=["Reflectance", "Ratio"],
)

tot_slider = RangeSlider(start=250, end=2500, value=(250, 2500), step=1,
                         title="Total Reflectance Wavelength Range (nm)")
spec_slider = RangeSlider(start=10, end=160, value=(10, 160), step=1,
                          title="Specular Reflectance Angle Range")
lamb_slider = RangeSlider(start=10, end=90, value=(10, 90), step=1,
                          title="Lambertian Reflectance Angle Range")
resid_slider = RangeSlider(start=10, end=90, value=(10, 90), step=1,
                           title="Lambertian Residual Angle Range")

totb_button = Button(label="Download Black Total Reflectance", button_type="success")
totw_button = Button(label="Download White Total Reflectance", button_type="success")
spec_button = Button(label="Download Specular Reflectance", button_type="success")
spec_rat_button = Button(label="Download Specular Ratio", button_type="success")
lamb_button = Button(label="Download Lambertian Reflectance", button_type="success")
resid_button = Button(label="Download Lambertian Residual", button_type="success")
selec_button = Button(label="Download Selected Materials", button_type="primary")

# ---------------------------------------------------------------------------
# CustomJS callbacks (all client-side -- no Python server needed)
# ---------------------------------------------------------------------------

# --- Material color filter ---
mat_color_js = CustomJS(
    args=dict(
        all_renderers=all_renderers,
        black_renderers=all_black_renderers,
        white_renderers=all_white_renderers,
        tot_label=tot_fig_label,
        spec_label=spec_fig_label,
        lamb_label=lamb_fig_label,
        spec_select=spec_select,
    ),
    code="""
    const val = cb_obj.value;
    if (val === 'Select Material') {
        for (const r of all_renderers) r.visible = false;
        tot_label.visible = true;
        spec_label.visible = true;
        lamb_label.visible = true;
        spec_select.disabled = true;
    } else if (val === 'All') {
        for (const r of all_renderers) r.visible = true;
        tot_label.visible = false;
        spec_label.visible = false;
        lamb_label.visible = false;
        spec_select.disabled = false;
    } else {
        const is_white = val === 'White';
        for (const r of black_renderers) r.visible = !is_white;
        for (const r of white_renderers) r.visible = is_white;
        spec_select.disabled = is_white;
        spec_label.visible = is_white;
        tot_label.visible = false;
        lamb_label.visible = !is_white;
    }
    """,
)
mat_color_select.js_on_change("value", mat_color_js)

# --- Specular variable type ---
spec_type_js = CustomJS(
    args=dict(
        ratio_renderers=black_spec_ratio_renderers,
        ref_renderers=black_spec_ref_renderers,
        spec_yaxis=spec_fig.yaxis[0],
    ),
    code="""
    const is_ratio = cb_obj.value === 'Ratio';
    spec_yaxis.axis_label = is_ratio ? 'Specular Ratio (%)' : 'Specular Reflectance';
    for (const r of ratio_renderers) r.visible = is_ratio;
    for (const r of ref_renderers) r.visible = !is_ratio;
    """,
)
spec_select.js_on_change("value", spec_type_js)

# --- Multi-choice material selector ---
multi_choice_js = CustomJS(
    args=dict(
        all_renderers=all_renderers,
        multi_choice=multi_choice,
        tot_renderers=black_tot_renderers + white_tot_renderers,
        spec_renderers=black_spec_ref_renderers,
        lamb_renderers=white_lamb_renderers,
        tot_label=tot_fig_label,
        spec_label=spec_fig_label,
        lamb_label=lamb_fig_label,
    ),
    code="""
    const selected = new Set(multi_choice.value);
    for (const r of all_renderers) {
        r.visible = selected.has(r.name);
    }
    function noData(renderers) {
        for (const r of renderers) { if (r.visible) return false; }
        return true;
    }
    tot_label.visible = noData(tot_renderers);
    spec_label.visible = noData(spec_renderers);
    lamb_label.visible = noData(lamb_renderers);
    """,
)
multi_choice.js_on_change("value", multi_choice_js)

# --- Range sliders ---
for slider, fig_range in [
    (tot_slider, total_fig.x_range),
    (spec_slider, spec_fig.x_range),
    (lamb_slider, lamb_fig.x_range),
    (resid_slider, lamb_resid_fig.x_range),
]:
    slider.js_on_change("value", CustomJS(
        args=dict(x_range=fig_range),
        code="x_range.start = cb_obj.value[0]; x_range.end = cb_obj.value[1];",
    ))

# --- Download buttons ---
DOWNLOAD_JS = """
function dataToCsv(source) {
    const columns = Object.keys(source.data);
    const nrows = source.get_length();
    const lines = [columns.join(",")];
    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const col of columns) row.push(source.data[col][i]);
        lines.push(row.join(","));
    }
    return lines.join("\\n") + "\\n";
}
const blob = new Blob([dataToCsv(source)], {type: "text/csv;charset=utf-8;"});
const link = document.createElement("a");
link.href = URL.createObjectURL(blob);
link.download = "reflectance_data.csv";
link.style.display = "none";
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
"""

SELEC_DOWNLOAD_JS = """
const columns = [];
const rndIndices = [];
let idx = 0;
for (const group of groups) {
    for (const activeIdx of group.active) {
        columns.push(group.labels[activeIdx]);
        rndIndices.push(activeIdx + idx);
    }
    idx += group.labels.length;
}
if (columns.length === 0) {
    alert("No materials selected. Please select at least one material.");
} else {
    const lines = [columns.join(",")];
    const nrows = rnds[rndIndices[0]].data_source.get_length();
    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const ri of rndIndices) {
            const r = rnds[ri];
            const v = r.data_source.data[r.name][i];
            row.push(v != null && v > -1 ? v : "");
        }
        lines.push(row.join(","));
    }
    const blob = new Blob([lines.join("\\n") + "\\n"], {type: "text/csv;charset=utf-8;"});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "selected_materials.csv";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
"""

totb_button.js_on_click(CustomJS(args=dict(source=black_tot_ds), code=DOWNLOAD_JS))
totw_button.js_on_click(CustomJS(args=dict(source=white_tot_ds), code=DOWNLOAD_JS))
spec_button.js_on_click(CustomJS(args=dict(source=black_spec_ref_ds), code=DOWNLOAD_JS))
spec_rat_button.js_on_click(CustomJS(args=dict(source=black_spec_ratio_ds), code=DOWNLOAD_JS))
lamb_button.js_on_click(CustomJS(args=dict(source=white_lamb_scaled_ds), code=DOWNLOAD_JS))
resid_button.js_on_click(CustomJS(args=dict(source=white_lamb_res_ds), code=DOWNLOAD_JS))
selec_button.js_on_click(
    CustomJS(args=dict(groups=checkbox_groups, rnds=all_renderers), code=SELEC_DOWNLOAD_JS)
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
  <em>Downloads</em> tab to export CSV files.</p>
</details>
<details>
  <summary><b>Plot Tools</b></summary>
  <p>Each plot has a toolbar with box zoom, pan, wheel zoom, reset, and save.
  Hover over lines to see material name and values.</p>
</details>
""")

instr_layout = column(instructions, filter_help, sizing_mode="stretch_width")
filter_layout = row(mat_color_select, spec_select, multi_choice, sizing_mode="stretch_width")
slider_layout = column(tot_slider, spec_slider, lamb_slider, resid_slider, sizing_mode="stretch_width")
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

tabs = Tabs(tabs=[
    TabPanel(child=instr_layout, title="Instructions"),
    TabPanel(child=filter_layout, title="Filters"),
    TabPanel(child=slider_layout, title="Range Sliders"),
    TabPanel(child=download_select_layout, title="Select Data"),
    TabPanel(child=download_buttons_layout, title="Downloads"),
], active=0)

page_layout = column(
    tabs,
    total_fig,
    spec_fig,
    row(lamb_fig, lamb_resid_fig, sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------
PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {{ bokeh_css }}
    {{ bokeh_js }}
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f5f5f5; color: #333;
        }
        .top-nav {
            background-color: #500000; color: #fff;
            padding: 12px 24px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .top-nav a { color: #fff; text-decoration: none; margin-left: 20px; font-size: 14px; }
        .top-nav a:hover { opacity: 0.8; }
        .nav-links { display: flex; align-items: center; gap: 16px; }
        .page-container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
        .page-title { font-size: 24px; font-weight: 700; margin: 0 0 20px 0; }
        .card {
            background: #fff; border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            padding: 16px; margin-bottom: 20px;
        }
        .bk-btn-success {
            color: #fff; background-color: #26a69a; border: none;
            border-radius: 4px; padding: 8px 16px; cursor: pointer;
            transition: background-color 0.2s; font-size: 13px; margin: 4px 0;
        }
        .bk-btn-success:hover { background-color: #2bbbad; }
        .bk-btn-primary {
            color: #fff; background-color: #500000; border: none;
            border-radius: 4px; padding: 8px 16px; cursor: pointer;
            transition: background-color 0.2s; font-size: 13px; margin: 4px 0;
        }
        .bk-btn-primary:hover { background-color: #700000; }
    </style>
</head>
<body>
    <nav class="top-nav">
        <span style="font-weight:700; font-size:18px;">Texas A&amp;M Instrumentation Lab</span>
        <div class="nav-links">
            <a href="https://instrumentation.tamu.edu/">Lab Home</a>
            <a href="https://github.com/matthewholden01/reflectance-plots">GitHub</a>
        </div>
    </nav>
    <div class="page-container">
        <h1 class="page-title">Black &amp; White Materials Reflectance Data</h1>
        <div class="card">
            {{ plot_div }}
        </div>
    </div>
    {{ plot_script }}
</body>
</html>
"""

from jinja2 import Template

html = file_html(page_layout, resources=CDN, title="B/W Materials Reflectance Data")

# Wrap the Bokeh output in our custom page template.
# file_html produces a full page; we extract the components and re-template.
from bokeh.embed import components

script, div = components(page_layout)
template = Template(PAGE_TEMPLATE)
final_html = template.render(
    title="B/W Materials Reflectance Data",
    bokeh_css=CDN.render_css(),
    bokeh_js=CDN.render_js(),
    plot_div=div,
    plot_script=script,
)

os.makedirs(OUT_DIR, exist_ok=True)
out_path = join(OUT_DIR, "index.html")
with open(out_path, "w") as f:
    f.write(final_html)

print(f"Built standalone page: {out_path}")
print(f"File size: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")
